"""Tests for CategoryService."""

import pytest
from questiontrail.services.category_service import CategoryService
from questiontrail.llm.contracts import ProviderError, ProviderErrorKind
from questiontrail.llm.mock import MockAdapter
from questiontrail.llm.router import Router
from questiontrail.services.structured_generation import StructuredGenerationService


def test_empty_objective_raises_value_error():
    service = CategoryService()
    with pytest.raises(ValueError):
        service.propose_categories("   ")


def test_scholarship_objective_deterministic_fallback():
    service = CategoryService(generation_service=None)
    categories = service.propose_categories("Evaluate Reliance Foundation Scholarship criteria")
    assert len(categories) >= 3
    assert all(c.enabled for c in categories)
    assert all(c.is_ai_suggested for c in categories)
    ids = [c.id for c in categories]
    assert "cat-eligibility-criteria" in ids
    assert "cat-financial-benefits" in ids


def test_generic_objective_deterministic_fallback():
    service = CategoryService(generation_service=None)
    categories = service.propose_categories("Analyze electric vehicle battery degradation models")
    assert len(categories) >= 3
    ids = [c.id for c in categories]
    assert "cat-core-claims" in ids
    assert "cat-source-consistency" in ids


def test_structured_llm_proposal_success():
    mock_payload = {
        "categories": [
            {
                "name": "Safety Protocols",
                "description": "Safety operational limits and guidelines.",
                "evaluation_question": "What safety standards are documented?",
            },
            {
                "name": "Thermal Thresholds",
                "description": "Operating temperatures and heat limits.",
                "evaluation_question": "What are maximum safe temperature ranges?",
            },
        ]
    }
    adapter = MockAdapter(fixed_response=mock_payload)
    router = Router([adapter])
    gen_service = StructuredGenerationService(router)
    service = CategoryService(generation_service=gen_service)

    categories = service.propose_categories("Evaluate battery thermal safety")
    assert len(categories) == 2
    assert categories[0].name == "Safety Protocols"
    assert categories[0].id == "cat-safety-protocols"
    assert categories[0].evaluation_question == "What safety standards are documented?"
    assert categories[1].name == "Thermal Thresholds"
    assert categories[1].id == "cat-thermal-thresholds"


def test_structured_llm_error_falls_back_gracefully():
    # Adapter raises ProviderError -> should fallback rather than crash
    err = ProviderError(
        kind=ProviderErrorKind.unavailable,
        provider="mock",
        message="Simulated model failure",
    )
    adapter = MockAdapter(raise_error=err)
    router = Router([adapter])
    gen_service = StructuredGenerationService(router)
    service = CategoryService(generation_service=gen_service)

    categories = service.propose_categories("Assess scholarship application guidelines")
    assert len(categories) >= 3
    assert any("eligibility" in c.id for c in categories)
