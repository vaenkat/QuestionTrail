"""Provider-neutral structured generation protocol and typed provider errors.

DESIGN RULES:
- No provider-specific logic here; this module is imported by all adapters.
- No API keys are read at module import time.
- No network calls happen during construction.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


# --- Error taxonomy ---

class ProviderErrorKind(str, Enum):
    """Typed error categories enabling precise failover and observability."""
    authentication = "authentication"          # 401 / 403: bad or missing key
    rate_limit = "rate_limit"                  # 429: quota or token-rate exceeded
    timeout = "timeout"                        # Request/response timeout
    unavailable = "unavailable"                # 5xx / model offline / service down
    invalid_response = "invalid_response"      # Malformed JSON or schema mismatch
    invalid_request = "invalid_request"        # Bad request built by adapter
    unknown = "unknown"                        # Unclassified failure


class ProviderError(Exception):
    """Structured, observable provider failure preserving all failure context."""

    def __init__(
        self,
        kind: ProviderErrorKind,
        provider: str,
        message: str,
        status_code: int | None = None,
        raw_response: str | None = None,
        cause: BaseException | None = None
    ) -> None:
        super().__init__(message)
        self.kind = kind
        self.provider = provider
        self.message = message
        self.status_code = status_code
        self.raw_response = raw_response
        self.cause = cause

    def __repr__(self) -> str:
        return (
            f"ProviderError(kind={self.kind.value!r}, provider={self.provider!r}, "
            f"message={self.message!r}, status_code={self.status_code})"
        )


# --- Shared request/response contracts ---

class GenerationRequest(BaseModel):
    """Provider-neutral structured generation request.

    Adapters translate these fields to their vendor wire format.
    No provider-specific parameters are permitted here.
    """
    system_prompt: str = Field(
        default="You are a precise research assistant. Respond only with valid JSON matching the requested schema.",
        description="System instruction for structured output"
    )
    user_prompt: str = Field(..., min_length=1, description="Task-specific instruction")
    response_schema: dict[str, Any] = Field(..., description="JSON Schema describing expected output structure")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0, description="Generation temperature")
    max_tokens: int = Field(default=2048, ge=1, le=8192, description="Maximum output tokens")


class AttemptRecord(BaseModel):
    """Metadata record for one provider invocation attempt."""
    provider: str
    model: str
    succeeded: bool
    error_kind: ProviderErrorKind | None = None
    error_message: str | None = None
    status_code: int | None = None


class GenerationResult(BaseModel):
    """Provider-neutral structured generation result with full provenance."""
    content: Any = Field(..., description="Validated response content (dict, list, or scalar)")
    raw_text: str = Field(..., description="Raw text returned by provider before parsing")
    provider: str = Field(..., description="Provider that produced the response")
    model: str = Field(..., description="Model identifier used")
    mode: str = Field(default="live", description="'live', 'mock', or 'precomputed'")
    attempts: list[AttemptRecord] = Field(
        default_factory=list,
        description="Ordered list of provider attempts made to produce this result"
    )


# --- Adapter Protocol ---

class LLMAdapterProtocol:
    """Abstract base class defining the provider adapter contract.

    Subclasses MUST NOT read API keys or perform network calls at __init__ time.
    """

    @property
    def provider_name(self) -> str:
        raise NotImplementedError

    @property
    def model_name(self) -> str:
        raise NotImplementedError

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Execute structured generation request. May raise ProviderError."""
        raise NotImplementedError
