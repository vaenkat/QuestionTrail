"""Shared pytest fixtures for the LLM router and generation service tests."""

import pytest

from questiontrail.llm.contracts import (
    GenerationRequest,
    ProviderError,
    ProviderErrorKind,
)
from questiontrail.llm.mock import MockAdapter
from questiontrail.llm.router import Router
from questiontrail.services.structured_generation import StructuredGenerationService


# --- Schema fixture ---

SIMPLE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "score": {"type": "integer"},
    },
    "required": ["title", "score"],
}

SIMPLE_REQUEST = GenerationRequest(
    user_prompt="Rate this source on a scale of 0-10.",
    response_schema=SIMPLE_SCHEMA,
)


# --- Adapter fixtures ---

@pytest.fixture()
def mock_adapter():
    return MockAdapter(fixed_response={"title": "Test Source", "score": 7})


@pytest.fixture()
def mock_adapter_auth_error():
    return MockAdapter(
        raise_error=ProviderError(
            kind=ProviderErrorKind.authentication,
            provider="mock",
            message="Bad key",
        )
    )


@pytest.fixture()
def mock_adapter_rate_limit():
    return MockAdapter(
        raise_error=ProviderError(
            kind=ProviderErrorKind.rate_limit,
            provider="mock",
            message="Quota exceeded",
        )
    )


@pytest.fixture()
def mock_adapter_timeout():
    return MockAdapter(
        raise_error=ProviderError(
            kind=ProviderErrorKind.timeout,
            provider="mock",
            message="Timed out",
        )
    )


@pytest.fixture()
def mock_adapter_unavailable():
    return MockAdapter(
        raise_error=ProviderError(
            kind=ProviderErrorKind.unavailable,
            provider="mock",
            message="Service is down",
        )
    )


@pytest.fixture()
def mock_adapter_invalid_response():
    return MockAdapter(
        raise_error=ProviderError(
            kind=ProviderErrorKind.invalid_response,
            provider="mock",
            message="Not valid JSON",
        )
    )


@pytest.fixture()
def success_router(mock_adapter):
    return Router([mock_adapter])


@pytest.fixture()
def generation_service(success_router):
    return StructuredGenerationService(success_router)
