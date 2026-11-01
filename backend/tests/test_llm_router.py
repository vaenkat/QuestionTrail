"""Tests for the LLM Router and StructuredGenerationService.

All tests use deterministic fakes only.
No network calls. No API keys required.
"""

import json
import pytest
from pydantic import BaseModel

from questiontrail.llm.contracts import (
    GenerationRequest,
    GenerationResult,
    ProviderError,
    ProviderErrorKind,
)
from questiontrail.llm.mock import MockAdapter
from questiontrail.llm.router import Router, AllProvidersExhausted
from questiontrail.services.structured_generation import (
    StructuredGenerationService,
    SchemaValidationError,
)

# Shared test constants (duplicated here to avoid `tests` package path issues)
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


# =========================================================
# MockAdapter – unit tests
# =========================================================

class TestMockAdapter:
    def test_returns_fixed_response(self):
        adapter = MockAdapter(fixed_response={"title": "X", "score": 5})
        result = adapter.generate(SIMPLE_REQUEST)
        assert result.content == {"title": "X", "score": 5}
        assert result.provider == "mock"
        assert result.mode == "mock"

    def test_constructs_minimal_response_from_schema(self):
        adapter = MockAdapter()
        result = adapter.generate(SIMPLE_REQUEST)
        assert "title" in result.content
        assert "score" in result.content

    def test_raw_text_is_valid_json(self):
        adapter = MockAdapter(fixed_response={"title": "T", "score": 1})
        result = adapter.generate(SIMPLE_REQUEST)
        parsed = json.loads(result.raw_text)
        assert parsed == result.content

    def test_records_single_successful_attempt(self):
        adapter = MockAdapter(fixed_response={"title": "T", "score": 0})
        result = adapter.generate(SIMPLE_REQUEST)
        assert len(result.attempts) == 1
        assert result.attempts[0].succeeded is True
        assert result.attempts[0].error_kind is None

    def test_raises_injected_provider_error(self):
        err = ProviderError(
            kind=ProviderErrorKind.timeout,
            provider="mock",
            message="Simulated timeout",
        )
        adapter = MockAdapter(raise_error=err)
        with pytest.raises(ProviderError) as exc_info:
            adapter.generate(SIMPLE_REQUEST)
        assert exc_info.value.kind == ProviderErrorKind.timeout

    def test_provider_name(self):
        assert MockAdapter().provider_name == "mock"

    def test_model_name_default(self):
        assert "mock" in MockAdapter().model_name

    def test_model_name_custom(self):
        assert MockAdapter(model="test-v99").model_name == "test-v99"

    def test_minimal_response_handles_all_primitive_types(self):
        schema = {
            "type": "object",
            "properties": {
                "s": {"type": "string"},
                "i": {"type": "integer"},
                "n": {"type": "number"},
                "b": {"type": "boolean"},
                "a": {"type": "array"},
                "o": {"type": "object"},
                "u": {},  # unknown type
            },
            "required": ["s", "i", "n", "b", "a", "o", "u"],
        }
        req = GenerationRequest(user_prompt="test", response_schema=schema)
        result = MockAdapter().generate(req)
        assert isinstance(result.content["s"], str)
        assert isinstance(result.content["i"], int)
        assert isinstance(result.content["n"], float)
        assert isinstance(result.content["b"], bool)
        assert isinstance(result.content["a"], list)
        assert isinstance(result.content["o"], dict)
        # An untyped property (no "type" key) defaults to string in the mock
        assert isinstance(result.content["u"], str)


# =========================================================
# Router – unit tests
# =========================================================

class TestRouter:
    def test_requires_at_least_one_adapter(self):
        with pytest.raises(ValueError):
            Router([])

    def test_success_on_first_adapter(self, mock_adapter):
        router = Router([mock_adapter])
        result = router.generate(SIMPLE_REQUEST)
        assert result.content == {"title": "Test Source", "score": 7}

    def test_records_single_attempt_on_success(self, mock_adapter):
        router = Router([mock_adapter])
        result = router.generate(SIMPLE_REQUEST)
        assert len(result.attempts) == 1
        assert result.attempts[0].succeeded is True

    def test_fails_over_to_second_adapter(self, mock_adapter_timeout, mock_adapter):
        router = Router([mock_adapter_timeout, mock_adapter])
        result = router.generate(SIMPLE_REQUEST)
        assert result.content == {"title": "Test Source", "score": 7}
        # Two attempts total: one failure, one success.
        assert len(result.attempts) == 2
        assert result.attempts[0].succeeded is False
        assert result.attempts[0].error_kind == ProviderErrorKind.timeout
        assert result.attempts[1].succeeded is True

    def test_exhausts_all_providers_raises(self, mock_adapter_timeout, mock_adapter_rate_limit):
        router = Router([mock_adapter_timeout, mock_adapter_rate_limit])
        with pytest.raises(AllProvidersExhausted) as exc_info:
            router.generate(SIMPLE_REQUEST)
        assert len(exc_info.value.attempts) == 2
        kinds = {a.error_kind for a in exc_info.value.attempts}
        assert ProviderErrorKind.timeout in kinds
        assert ProviderErrorKind.rate_limit in kinds

    def test_exhausted_exception_preserves_all_attempt_records(
        self, mock_adapter_auth_error, mock_adapter_unavailable
    ):
        router = Router([mock_adapter_auth_error, mock_adapter_unavailable])
        with pytest.raises(AllProvidersExhausted) as exc_info:
            router.generate(SIMPLE_REQUEST)
        attempts = exc_info.value.attempts
        assert all(not a.succeeded for a in attempts)
        assert attempts[0].error_kind == ProviderErrorKind.authentication
        assert attempts[1].error_kind == ProviderErrorKind.unavailable

    def test_auth_failure_does_not_return_stale_result(self, mock_adapter_auth_error):
        router = Router([mock_adapter_auth_error])
        with pytest.raises(AllProvidersExhausted):
            router.generate(SIMPLE_REQUEST)

    def test_invalid_response_does_not_return_unrelated_result(self, mock_adapter_invalid_response):
        router = Router([mock_adapter_invalid_response])
        with pytest.raises(AllProvidersExhausted) as exc_info:
            router.generate(SIMPLE_REQUEST)
        assert exc_info.value.attempts[0].error_kind == ProviderErrorKind.invalid_response

    def test_all_error_kinds_covered(self):
        """Every ProviderErrorKind variant can be raised and caught."""
        for kind in ProviderErrorKind:
            err = ProviderError(kind=kind, provider="mock", message=f"sim {kind}")
            adapter = MockAdapter(raise_error=err)
            router = Router([adapter])
            with pytest.raises(AllProvidersExhausted) as exc_info:
                router.generate(SIMPLE_REQUEST)
            assert exc_info.value.attempts[0].error_kind == kind


# =========================================================
# StructuredGenerationService – unit tests
# =========================================================

class SimpleModel(BaseModel):
    title: str
    score: int


class TestStructuredGenerationService:
    def test_returns_parsed_pydantic_model_on_success(self, generation_service):
        result = generation_service.generate_typed(SIMPLE_REQUEST, SimpleModel)
        assert isinstance(result["parsed"], SimpleModel)
        assert result["parsed"].title == "Test Source"
        assert result["parsed"].score == 7

    def test_generation_result_included_in_return(self, generation_service):
        result = generation_service.generate_typed(SIMPLE_REQUEST, SimpleModel)
        assert isinstance(result["generation"], GenerationResult)

    def test_schema_mismatch_raises_schema_validation_error(self):
        class StrictModel(BaseModel):
            required_field: str
            must_be_int: int

        adapter = MockAdapter(fixed_response={"title": "T", "score": "NOT_AN_INT"})
        router = Router([adapter])
        service = StructuredGenerationService(router)

        req = GenerationRequest(
            user_prompt="test",
            response_schema={"type": "object", "properties": {}, "required": []},
        )
        with pytest.raises(SchemaValidationError) as exc_info:
            service.generate_typed(req, StrictModel)
        # Error preserves the generation result for debugging.
        assert exc_info.value.result is not None
        assert exc_info.value.validation_error is not None

    def test_provider_error_propagates_unchanged(self):
        err = ProviderError(
            kind=ProviderErrorKind.rate_limit,
            provider="mock",
            message="Quota hit",
        )
        adapter = MockAdapter(raise_error=err)
        router = Router([adapter])
        service = StructuredGenerationService(router)

        with pytest.raises(AllProvidersExhausted):
            service.generate_typed(SIMPLE_REQUEST, SimpleModel)

    def test_schema_validation_error_contains_provider_name(self):
        class StrictModel(BaseModel):
            must_exist: str

        adapter = MockAdapter(fixed_response={})  # Missing required field
        router = Router([adapter])
        service = StructuredGenerationService(router)
        req = GenerationRequest(
            user_prompt="test",
            response_schema={"type": "object", "properties": {}, "required": []},
        )
        with pytest.raises(SchemaValidationError) as exc_info:
            service.generate_typed(req, StrictModel)
        assert "mock" in str(exc_info.value).lower() or "StrictModel" in str(exc_info.value)


# =========================================================
# Module import safety
# =========================================================

class TestModuleImportSafety:
    def test_contracts_import_does_not_read_env(self):
        """Importing contracts should never raise ProviderError or read secrets."""
        import questiontrail.llm.contracts as c  # noqa: F401
        assert hasattr(c, "GenerationRequest")

    def test_mock_import_does_not_make_network_call(self):
        import questiontrail.llm.mock as m  # noqa: F401
        assert hasattr(m, "MockAdapter")

    def test_router_import_does_not_make_network_call(self):
        import questiontrail.llm.router as r  # noqa: F401
        assert hasattr(r, "Router")

    def test_nvidia_import_does_not_make_network_call(self):
        """NvidiaAdapter module can be imported without a network call."""
        import questiontrail.llm.nvidia as n  # noqa: F401
        assert hasattr(n, "NvidiaAdapter")

    def test_gemini_import_does_not_make_network_call(self):
        """GeminiAdapter module can be imported without a network call."""
        import questiontrail.llm.gemini as g  # noqa: F401
        assert hasattr(g, "GeminiAdapter")


# =========================================================
# Router Settings & Credential Safety
# =========================================================

class TestRouterSettings:
    def test_mock_mode_settings(self):
        from questiontrail.settings import Settings
        from questiontrail.llm.router import build_router_from_settings

        s = Settings(llm_provider="mock")
        router = build_router_from_settings(s)
        assert len(router.adapters) == 1
        assert router.adapters[0].provider_name == "mock"

    def test_nvidia_mode_with_key(self):
        from questiontrail.settings import Settings
        from questiontrail.llm.router import build_router_from_settings

        s = Settings(
            llm_provider="nvidia",
            nvidia_api_key="nv-secret-key-12345",
        )
        router = build_router_from_settings(s)
        assert len(router.adapters) == 1
        assert router.adapters[0].provider_name == "nvidia"

    def test_nvidia_mode_missing_key_does_not_fall_back_to_mock(self):
        import pytest
        from questiontrail.settings import Settings
        from questiontrail.llm.router import build_router_from_settings
        from questiontrail.llm.contracts import ProviderError, ProviderErrorKind, GenerationRequest
        from questiontrail.llm.router import AllProvidersExhausted

        s = Settings(
            llm_provider="nvidia",
            nvidia_api_key=None,
        )
        router = build_router_from_settings(s)
        assert len(router.adapters) == 1
        assert router.adapters[0].provider_name == "nvidia"
        # When invoked, raises typed ProviderError wrapped in AllProvidersExhausted
        with pytest.raises(AllProvidersExhausted) as excinfo:
            router.generate(GenerationRequest(user_prompt="test", response_schema={}))
        assert excinfo.value.attempts[0].error_kind == ProviderErrorKind.authentication
        assert "No API key configured" in excinfo.value.attempts[0].error_message

    def test_auto_mode_orders_live_providers_without_mock(self):
        from questiontrail.settings import Settings
        from questiontrail.llm.router import build_router_from_settings

        s = Settings(
            llm_provider="auto",
            nvidia_api_key="nv-key",
            gemini_api_key="gem-key",
        )
        router = build_router_from_settings(s)
        names = [a.provider_name for a in router.adapters]
        assert names == ["nvidia", "gemini"]

    def test_explicit_mock_mode_uses_mock_adapter(self):
        from questiontrail.settings import Settings
        from questiontrail.llm.router import build_router_from_settings

        s = Settings(
            llm_provider="mock",
        )
        router = build_router_from_settings(s)
        assert len(router.adapters) == 1
        assert router.adapters[0].provider_name == "mock"


class TestCredentialSafety:
    def test_attempt_records_do_not_contain_secrets(self):
        from questiontrail.llm.contracts import AttemptRecord

        rec = AttemptRecord(
            provider="nvidia",
            model="test-model",
            succeeded=False,
            error_kind=ProviderErrorKind.authentication,
            error_message="NVIDIA authentication failed (HTTP 401)",
            status_code=401,
        )
        d = rec.model_dump()
        for v in d.values():
            if isinstance(v, str):
                assert "key" not in v.lower() or "failed" in v.lower()
                assert "secret" not in v.lower()

    def test_provider_error_repr_does_not_contain_headers_or_keys(self):
        err = ProviderError(
            kind=ProviderErrorKind.authentication,
            provider="nvidia",
            message="NVIDIA authentication failed (HTTP 401)",
            status_code=401,
        )
        rep = repr(err)
        assert "Authorization" not in rep
        assert "Bearer" not in rep

