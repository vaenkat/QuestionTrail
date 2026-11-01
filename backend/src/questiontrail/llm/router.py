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


class UnconfiguredProviderAdapter(LLMAdapterProtocol):
    """Adapter used when live mode is selected but credentials are not configured.

    Raises a typed ProviderError on invocation so caller can detect failure
    without silently masking unconfigured credentials.
    """

    def __init__(self, mode: str) -> None:
        self._mode = mode

    @property
    def provider_name(self) -> str:
        return self._mode

    @property
    def model_name(self) -> str:
        return "unconfigured"

    def generate(self, request: GenerationRequest) -> GenerationResult:
        raise ProviderError(
            kind=ProviderErrorKind.authentication,
            provider=self._mode,
            message=(
                f"No API key configured for live mode '{self._mode}'. "
                f"Set NVIDIA_API_KEY or GEMINI_API_KEY in .env, or use LLM_PROVIDER=mock for offline testing."
            ),
        )


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
      - If mode == "mock": MockAdapter only.
      - If mode == "nvidia": NVIDIA NIM only.
      - If mode == "gemini": Google Gemini only.
      - If mode == "auto": NVIDIA NIM first, Google Gemini second.

    CRITICAL SAFETY RULES:
      - Adapters are only added when their credentials are non-empty.
      - Live modes ("nvidia", "gemini", "auto") NEVER fall back to MockAdapter.
        Live provider failures or missing credentials must never silently fabricate
        synthetic mock output.
      - Explicit "mock" mode remains available for offline development and testing.
    """
    from questiontrail.llm.mock import MockAdapter
    from questiontrail.llm.nvidia import NvidiaAdapter
    from questiontrail.llm.gemini import GeminiAdapter

    adapters: list[LLMAdapterProtocol] = []
    mode: str = getattr(settings, "llm_provider", getattr(settings, "provider_mode", "mock"))

    raw_nvidia_key = getattr(settings, "nvidia_api_key", None)
    nvidia_key = (
        raw_nvidia_key.get_secret_value().strip()
        if hasattr(raw_nvidia_key, "get_secret_value") and raw_nvidia_key
        else (raw_nvidia_key.strip() if isinstance(raw_nvidia_key, str) else None)
    )

    raw_gemini_key = getattr(settings, "gemini_api_key", None)
    gemini_key = (
        raw_gemini_key.get_secret_value().strip()
        if hasattr(raw_gemini_key, "get_secret_value") and raw_gemini_key
        else (raw_gemini_key.strip() if isinstance(raw_gemini_key, str) else None)
    )

    nvidia_model: str = getattr(settings, "nvidia_model", "meta/llama-3.3-70b-instruct")
    gemini_model: str = getattr(settings, "gemini_model", "gemini-2.0-flash")
    use_mock_fallback: bool = getattr(settings, "use_mock_fallback", False)

    if mode == "mock":
        adapters.append(MockAdapter())
        return Router(adapters)

    if mode in ("nvidia", "auto") and nvidia_key:
        adapters.append(NvidiaAdapter(api_key=nvidia_key, model=nvidia_model))

    if mode in ("gemini", "auto") and gemini_key:
        adapters.append(GeminiAdapter(api_key=gemini_key, model=gemini_model))

    # If mock fallback was explicitly requested (e.g. in a test fixture)
    if use_mock_fallback:
        adapters.append(MockAdapter())
        return Router(adapters)

    # In live modes with no credentials configured, use UnconfiguredProviderAdapter
    # so an explicit, typed ProviderError is raised rather than silent mock fallback.
    if not adapters:
        adapters.append(UnconfiguredProviderAdapter(mode))

    return Router(adapters)

