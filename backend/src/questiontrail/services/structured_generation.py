"""Schema-validating structured generation service.

This service is the single entry-point for all analysis code that needs
structured output from a language model.

DESIGN RULES:
- Business logic never imports adapter modules directly; use this service.
- Schema validation is performed here on the router's raw content.
- All ProviderError instances are propagated as-is to preserve failure context.
- No API keys are read by this module; settings injection happens at app startup.
"""

from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError

from questiontrail.llm.contracts import (
    GenerationRequest,
    GenerationResult,
    ProviderError,
    ProviderErrorKind,
)
from questiontrail.llm.router import Router, AllProvidersExhausted

T = TypeVar("T", bound=BaseModel)


class SchemaValidationError(Exception):
    """Raised when the provider's structured output does not match the caller's schema.

    Wraps pydantic ValidationError and preserves the raw provider result so
    callers can inspect what was actually returned.
    """

    def __init__(
        self,
        message: str,
        result: GenerationResult,
        validation_error: ValidationError,
    ) -> None:
        super().__init__(message)
        self.result = result
        self.validation_error = validation_error


class StructuredGenerationService:
    """Schema-validating wrapper over the LLM Router.

    Usage::

        service = StructuredGenerationService(router)
        result = service.generate(request, MySchema)
        typed_obj: MySchema = result["parsed"]   # pydantic model instance
        gen_result: GenerationResult = result["generation"]
    """

    def __init__(self, router: Router) -> None:
        self._router = router

    def generate_typed(
        self,
        request: GenerationRequest,
        schema_model: Type[T],
    ) -> dict[str, Any]:
        """Generate and validate structured output against a Pydantic model.

        Returns a dict with keys:
          - "parsed": validated Pydantic model instance.
          - "generation": the GenerationResult (provider, model, attempts, raw_text).

        Raises:
          - ProviderError (or AllProvidersExhausted) if every provider fails.
          - SchemaValidationError if the provider returns data that doesn't match
            the schema_model (wraps ValidationError, preserves GenerationResult).
        """
        result = self._router.generate(request)
        try:
            parsed = schema_model.model_validate(result.content)
        except ValidationError as exc:
            raise SchemaValidationError(
                message=(
                    f"Provider '{result.provider}' returned content that does not "
                    f"match schema '{schema_model.__name__}': {exc}"
                ),
                result=result,
                validation_error=exc,
            ) from exc

        return {"parsed": parsed, "generation": result}
