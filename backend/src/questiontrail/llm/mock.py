"""Deterministic mock LLM adapter for automated testing.

Produces stable, configurable responses without any network calls.
No API key is read or required.
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


class MockAdapter(LLMAdapterProtocol):
    """Deterministic mock adapter.

    Behaviour:
    - Returns `fixed_response` if provided.
    - Otherwise constructs a minimal valid JSON object from the request schema.
    - Can be configured to raise a specific ProviderError on demand.
    """

    PROVIDER = "mock"

    def __init__(
        self,
        model: str = "mock-deterministic-v1",
        fixed_response: dict[str, Any] | None = None,
        raise_error: ProviderError | None = None,
    ) -> None:
        # No network calls; no secret reads at construction time.
        self._model = model
        self._fixed_response = fixed_response
        self._raise_error = raise_error

    @property
    def provider_name(self) -> str:
        return self.PROVIDER

    @property
    def model_name(self) -> str:
        return self._model

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if self._raise_error is not None:
            raise self._raise_error

        if self._fixed_response is not None:
            payload = self._fixed_response
        else:
            payload = self._minimal_schema_response(request.response_schema)

        raw_text = json.dumps(payload, separators=(",", ":"))
        return GenerationResult(
            content=payload,
            raw_text=raw_text,
            provider=self.PROVIDER,
            model=self._model,
            mode="mock",
            attempts=[
                AttemptRecord(
                    provider=self.PROVIDER,
                    model=self._model,
                    succeeded=True,
                )
            ],
        )

    @staticmethod
    def _minimal_schema_response(schema: dict[str, Any]) -> dict[str, Any]:
        """Produce a minimal JSON object satisfying a JSON Schema's required properties."""
        props: dict[str, Any] = schema.get("properties", {})
        required: list[str] = schema.get("required", list(props.keys()))
        result: dict[str, Any] = {}
        for key in required:
            prop_def = props.get(key, {})
            prop_type = prop_def.get("type", "string")
            if prop_type == "string":
                result[key] = f"mock_{key}"
            elif prop_type == "integer":
                result[key] = 0
            elif prop_type == "number":
                result[key] = 0.0
            elif prop_type == "boolean":
                result[key] = False
            elif prop_type == "array":
                result[key] = []
            elif prop_type == "object":
                result[key] = {}
            else:
                result[key] = None
        return result
