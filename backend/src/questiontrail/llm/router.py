"""LLM Router: settings-driven fallback across provider adapters.

DESIGN RULES:
- Fallback order comes from settings, not hardcoded logic.
- Each attempt is recorded in the result regardless of success or failure.
- Secrets are injected via Settings; this module never reads env vars directly.
- No network calls at construction time.
"""

from questiontrail.llm.contracts import (
    LLMAdapterProtocol,
    GenerationRequest,
    GenerationResult,
    AttemptRecord,
    ProviderError,
    ProviderErrorKind,
)


class AllProvidersExhausted(Exception):
    """Raised when every configured provider has failed."""

    def __init__(self, attempts: list[AttemptRecord]) -> None:
        kinds = [a.error_kind.value if a.error_kind else "?" for a in attempts]
        super().__init__(
            f"All {len(attempts)} provider attempt(s) failed: {', '.join(kinds)}"
        )
        self.attempts = attempts


class Router:
    """Routes GenerationRequest through an ordered adapter list.

    Failover:
    - Tries each adapter in order.
    - On ProviderError, records the attempt and continues to the next adapter.
    - On success, returns the result annotated with all recorded attempts.
    - Raises AllProvidersExhausted if every adapter fails; includes all attempt records.

    No cache eligibility logic lives here; the cache contract belongs to the
    analysis service which has access to full snapshot metadata.
    """

    def __init__(self, adapters: list[LLMAdapterProtocol]) -> None:
        if not adapters:
            raise ValueError("Router requires at least one adapter")
        self._adapters = adapters

    @property
    def adapters(self) -> list[LLMAdapterProtocol]:
        return list(self._adapters)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Execute structured generation with bounded fallover.

        Returns the first successful GenerationResult, enriched with all attempt
        records (including preceding failures).  Raises AllProvidersExhausted if
        every adapter fails.
        """
        accumulated_attempts: list[AttemptRecord] = []

        for adapter in self._adapters:
            try:
                result = adapter.generate(request)
                # Prepend failures that preceded this success.
                result.attempts = accumulated_attempts + result.attempts
                return result
            except ProviderError as exc:
                accumulated_attempts.append(
                    AttemptRecord(
                        provider=exc.provider,
                        model=adapter.model_name,
                        succeeded=False,
                        error_kind=exc.kind,
                        error_message=exc.message,
                        status_code=exc.status_code,
                    )
                )

        raise AllProvidersExhausted(accumulated_attempts)


def build_router_from_settings(settings: "Any") -> Router:  # type: ignore[name-defined]
    """Construct a Router from application Settings.

    Provider order:
      - If mode == "mock": mock-only.
      - If mode == "nvidia": NVIDIA first, mock fallback.
      - If mode == "gemini": Gemini first, mock fallback.
      - If mode == "auto": all configured live providers (with keys), then mock fallback.

    Adapters are only added when their credentials are present.
    SecretStr fields are safely unwrapped via get_secret_value().
    """
    from questiontrail.llm.mock import MockAdapter
    from questiontrail.llm.nvidia import NvidiaAdapter
    from questiontrail.llm.gemini import GeminiAdapter

    adapters: list[LLMAdapterProtocol] = []
    # Support both llm_provider and provider_mode attribute names
    mode: str = getattr(settings, "llm_provider", getattr(settings, "provider_mode", "mock"))

    raw_nvidia_key = getattr(settings, "nvidia_api_key", None)
    nvidia_key = (
        raw_nvidia_key.get_secret_value()
        if hasattr(raw_nvidia_key, "get_secret_value")
        else raw_nvidia_key
    )

    raw_gemini_key = getattr(settings, "gemini_api_key", None)
    gemini_key = (
        raw_gemini_key.get_secret_value()
        if hasattr(raw_gemini_key, "get_secret_value")
        else raw_gemini_key
    )

    nvidia_model: str = getattr(settings, "nvidia_model", "meta/llama-3.1-70b-instruct")
    gemini_model: str = getattr(settings, "gemini_model", "gemini-2.0-flash")
    use_mock_fallback: bool = getattr(settings, "use_mock_fallback", True)

    if mode == "mock":
        adapters.append(MockAdapter())
        return Router(adapters)

    if mode in ("nvidia", "auto") and nvidia_key:
        adapters.append(NvidiaAdapter(api_key=nvidia_key, model=nvidia_model))

    if mode in ("gemini", "auto") and gemini_key:
        adapters.append(GeminiAdapter(api_key=gemini_key, model=gemini_model))

    if not adapters or use_mock_fallback:
        adapters.append(MockAdapter())

    return Router(adapters)

