"""Thin Gemini adapter using the Google GenAI SDK's structured-output configuration.

DESIGN RULES:
- No network calls or secret reads at module import or __init__ time.
- API key is accepted at construction as an already-resolved string.
- Adapter uses google-genai SDK's response_schema feature for native structured output.
- All Gemini-specific errors are mapped to the typed ProviderError taxonomy.
"""

import json
from typing import Any

from questiontrail.llm.contracts import (
    LLMAdapterProtocol,
    GenerationRequest,
    GenerationResult,
    AttemptRecord,
    ProviderError,
    ProviderErrorKind,
)

_DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiAdapter(LLMAdapterProtocol):
    """Adapter for Google Gemini using the native SDK structured-output feature.

    Gemini supports native JSON schema enforcement via `response_schema` on the
    generation config, which is more reliable than prompt-based JSON extraction.
    The SDK client is lazily imported so this module remains importable without
    `google-genai` installed (unit tests use MockAdapter instead).
    """

    PROVIDER = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = _DEFAULT_MODEL,
        client: Any = None,          # Inject google.genai.Client for tests
    ) -> None:
        # Secret accepted as resolved string; never read from env here.
        self._api_key = api_key
        self._model = model
        # Defer real client construction to first generate() call.
        self._injected_client = client
        self._client: Any = None

    @property
    def provider_name(self) -> str:
        return self.PROVIDER

    @property
    def model_name(self) -> str:
        return self._model

    def _get_client(self) -> Any:
        """Return injected client or construct a real one on demand."""
        if self._injected_client is not None:
            return self._injected_client
        if self._client is not None:
            return self._client
        try:
            from google import genai  # type: ignore[import-untyped]
            self._client = genai.Client(api_key=self._api_key)
            return self._client
        except ImportError as exc:
            raise ProviderError(
                kind=ProviderErrorKind.unavailable,
                provider=self.PROVIDER,
                message="google-genai package is not installed. Run: uv add google-genai",
                cause=exc,
            ) from exc

    def generate(self, request: GenerationRequest) -> GenerationResult:
        client = self._get_client()

        combined_prompt = (
            f"{request.system_prompt}\n\n{request.user_prompt}"
        )

        try:
            from google.genai import types as genai_types  # type: ignore[import-untyped]
            response = client.models.generate_content(
                model=self._model,
                contents=combined_prompt,
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=request.response_schema,
                    temperature=request.temperature,
                    max_output_tokens=request.max_tokens,
                ),
            )
        except ImportError as exc:
            raise ProviderError(
                kind=ProviderErrorKind.unavailable,
                provider=self.PROVIDER,
                message="google-genai package is not installed.",
                cause=exc,
            ) from exc
        except Exception as exc:
            raise self._classify_sdk_error(exc) from exc

        raw_text = getattr(response, "text", None) or ""
        parsed = self._parse_response(raw_text, response)

        return GenerationResult(
            content=parsed,
            raw_text=raw_text,
            provider=self.PROVIDER,
            model=self._model,
            mode="live",
            attempts=[
                AttemptRecord(
                    provider=self.PROVIDER,
                    model=self._model,
                    succeeded=True,
                )
            ],
        )

    @staticmethod
    def _parse_response(raw_text: str, response: Any) -> Any:
        """Parse JSON from Gemini response text."""
        text = raw_text.strip()
        if not text:
            raise ProviderError(
                kind=ProviderErrorKind.invalid_response,
                provider="gemini",
                message="Gemini returned an empty response",
                raw_response=raw_text,
            )
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProviderError(
                kind=ProviderErrorKind.invalid_response,
                provider="gemini",
                message=f"Gemini response is not valid JSON: {exc}",
                raw_response=raw_text,
                cause=exc,
            ) from exc

    @staticmethod
    def _classify_sdk_error(exc: Exception) -> ProviderError:
        """Map google-genai SDK exceptions to the typed ProviderError taxonomy."""
        msg = str(exc)
        exc_type = type(exc).__name__

        if "API_KEY_INVALID" in msg or "PERMISSION_DENIED" in msg or "403" in msg:
            return ProviderError(
                kind=ProviderErrorKind.authentication,
                provider="gemini",
                message="Gemini authentication failed (invalid API key or permission denied)",
                cause=exc,
            )
        if "RESOURCE_EXHAUSTED" in msg or "429" in msg or "quota" in msg.lower():
            return ProviderError(
                kind=ProviderErrorKind.rate_limit,
                provider="gemini",
                message=f"Gemini rate limit / quota exceeded: {msg}",
                cause=exc,
            )
        if "timeout" in msg.lower() or "DeadlineExceeded" in exc_type or "Timeout" in exc_type:
            return ProviderError(
                kind=ProviderErrorKind.timeout,
                provider="gemini",
                message=f"Gemini request timed out: {msg}",
                cause=exc,
            )
        if "503" in msg or "ServiceUnavailable" in exc_type or "UNAVAILABLE" in msg:
            return ProviderError(
                kind=ProviderErrorKind.unavailable,
                provider="gemini",
                message=f"Gemini service unavailable: {msg}",
                cause=exc,
            )
        return ProviderError(
            kind=ProviderErrorKind.unknown,
            provider="gemini",
            message=f"Gemini unexpected error ({exc_type}): {msg}",
            cause=exc,
        )
