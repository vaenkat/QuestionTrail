"""LLM package public exports."""

from questiontrail.llm.contracts import (
    ProviderErrorKind,
    ProviderError,
    GenerationRequest,
    GenerationResult,
    AttemptRecord,
    LLMAdapterProtocol,
)
from questiontrail.llm.mock import MockAdapter
from questiontrail.llm.router import Router, AllProvidersExhausted, build_router_from_settings

__all__ = [
    "ProviderErrorKind",
    "ProviderError",
    "GenerationRequest",
    "GenerationResult",
    "AttemptRecord",
    "LLMAdapterProtocol",
    "MockAdapter",
    "Router",
    "AllProvidersExhausted",
    "build_router_from_settings",
]
