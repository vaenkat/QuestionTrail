"""Thin NVIDIA adapter targeting the OpenAI-compatible chat-completions endpoint.

DESIGN RULES:
- No network calls or secret reads at module import or __init__ time.
- API key is accepted at construction as an already-resolved string.
- Adapter translates GenerationRequest to NVIDIA's wire format; caller never sees NVIDIA specifics.
- All NVIDIA-specific errors are mapped to the typed ProviderError taxonomy.
"""

import json
import httpx

from questiontrail.llm.contracts import (
    LLMAdapterProtocol,
    GenerationRequest,
    GenerationResult,
    AttemptRecord,
    ProviderError,
    ProviderErrorKind,
)


_NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
_DEFAULT_MODEL = "meta/llama-3.1-70b-instruct"
_DEFAULT_TIMEOUT_S = 60.0


class NvidiaAdapter(LLMAdapterProtocol):
    """Adapter for the NVIDIA NIM OpenAI-compatible chat-completions endpoint.

    Structured output is requested via a JSON-mode system prompt; NVIDIA NIM
    does not universally support OpenAI's `response_format` parameter across
    all models, so we rely on prompt instruction + post-hoc JSON extraction.
    """

    PROVIDER = "nvidia"

    def __init__(
        self,
        api_key: str,
        model: str = _DEFAULT_MODEL,
        base_url: str = _NVIDIA_BASE_URL,
        timeout_seconds: float = _DEFAULT_TIMEOUT_S,
        http_client: httpx.Client | None = None,
    ) -> None:
        # Secret is accepted as an already-resolved string — never read from env here.
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        # Allow injection of a fake HTTP client for tests.
        self._http_client = http_client

    @property
    def provider_name(self) -> str:
        return self.PROVIDER

    @property
    def model_name(self) -> str:
        return self._model

    def generate(self, request: GenerationRequest) -> GenerationResult:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        schema_hint = json.dumps(request.response_schema, separators=(",", ":"))
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"{request.user_prompt}\n\n"
                        f"Respond ONLY with a valid JSON object matching this schema:\n{schema_hint}"
                    ),
                },
            ],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        client = self._http_client
        if client is None:
            client = httpx.Client(timeout=self._timeout)

        try:
            response = client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
        except httpx.TimeoutException as exc:
            raise ProviderError(
                kind=ProviderErrorKind.timeout,
                provider=self.PROVIDER,
                message=f"Request to NVIDIA timed out after {self._timeout}s",
                cause=exc,
            ) from exc
        except httpx.RequestError as exc:
            raise ProviderError(
                kind=ProviderErrorKind.unavailable,
                provider=self.PROVIDER,
                message=f"NVIDIA connection error: {exc}",
                cause=exc,
            ) from exc

        raw_text = response.text
        self._raise_for_http_status(response, raw_text)

        # Extract content from OpenAI-compatible response shape.
        try:
            data = response.json()
            text_content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise ProviderError(
                kind=ProviderErrorKind.invalid_response,
                provider=self.PROVIDER,
                message="Unexpected NVIDIA response structure",
                raw_response=raw_text,
                cause=exc,
            ) from exc

        parsed = self._parse_json_content(text_content, raw_text)
        return GenerationResult(
            content=parsed,
            raw_text=text_content,
            provider=self.PROVIDER,
            model=self._model,
            mode="live",
            attempts=[
                AttemptRecord(
                    provider=self.PROVIDER,
                    model=self._model,
                    succeeded=True,
                    status_code=response.status_code,
                )
            ],
        )

    def _raise_for_http_status(self, response: httpx.Response, raw_text: str) -> None:
        code = response.status_code
        if code == 200:
            return
        if code in (401, 403):
            raise ProviderError(
                kind=ProviderErrorKind.authentication,
                provider=self.PROVIDER,
                message=f"NVIDIA authentication failed (HTTP {code})",
                status_code=code,
                raw_response=raw_text,
            )
        if code == 429:
            raise ProviderError(
                kind=ProviderErrorKind.rate_limit,
                provider=self.PROVIDER,
                message=f"NVIDIA rate limit / quota exceeded (HTTP {code})",
                status_code=code,
                raw_response=raw_text,
            )
        if code >= 500:
            raise ProviderError(
                kind=ProviderErrorKind.unavailable,
                provider=self.PROVIDER,
                message=f"NVIDIA service unavailable (HTTP {code})",
                status_code=code,
                raw_response=raw_text,
            )
        raise ProviderError(
            kind=ProviderErrorKind.invalid_response,
            provider=self.PROVIDER,
            message=f"NVIDIA unexpected HTTP status {code}",
            status_code=code,
            raw_response=raw_text,
        )

    @staticmethod
    def _parse_json_content(text: str, raw_text: str) -> dict:
        """Extract and parse JSON from model text output."""
        text = text.strip()
        # Strip markdown code fences if present.
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderError(
                kind=ProviderErrorKind.invalid_response,
                provider="nvidia",
                message=f"NVIDIA response is not valid JSON: {exc}",
                raw_response=raw_text,
                cause=exc,
            ) from exc
