"""Category proposal service.

Generates structured, domain-neutral assessment categories from any free-text research objective.
Uses StructuredGenerationService with graceful deterministic fallback.
"""

import re
from typing import Any
from pydantic import BaseModel, Field

from questiontrail.domain.models import AssessmentCategory
from questiontrail.llm.contracts import GenerationRequest
from questiontrail.services.structured_generation import StructuredGenerationService


class CategoryProposalItem(BaseModel):
    """Single proposed category structure for LLM generation."""
    name: str = Field(..., min_length=2, description="Concise category title")
    description: str = Field(..., min_length=5, description="Scope and focus of this evaluation dimension")
    evaluation_question: str = Field(..., min_length=5, description="Clear guiding question to test evidence against")


class CategoryProposalOutput(BaseModel):
    """Root model for LLM structured output."""
    categories: list[CategoryProposalItem] = Field(
        ...,
        min_length=2,
        max_length=8,
        description="List of proposed evaluation dimensions"
    )


def _slugify(text: str) -> str:
    """Convert text into clean lowercase slug for ID."""
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower())
    return clean.strip("-")[:32] or "category"


CATEGORY_PROPOSAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "categories": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "evaluation_question": {"type": "string"},
                },
                "required": ["name", "description", "evaluation_question"],
            },
        }
    },
    "required": ["categories"],
}


class CategoryService:
    """Service to generate and validate assessment categories from research objectives."""

    def __init__(self, generation_service: StructuredGenerationService | None = None) -> None:
        self._gen_service = generation_service

    def propose_categories(self, objective: str) -> list[AssessmentCategory]:
        """Propose 3 to 6 evaluation categories for a given research objective.

        If a generation service is provided, requests structured output from the router.
        Falls back to deterministic heuristics if generation fails or is in mock mode.
        """
        stripped_obj = objective.strip()
        if not stripped_obj:
            raise ValueError("Research objective cannot be empty")

        if self._gen_service is not None:
            try:
                request = GenerationRequest(
                    system_prompt=(
                        "You are an expert research analyst. Propose 3 to 5 objective, evidence-based "
                        "evaluation categories to systematically investigate the user's research objective. "
                        "For each category, provide a concise name, description, and an exact evaluation question."
                    ),
                    user_prompt=f"Research objective:\n{stripped_obj}",
                    response_schema=CATEGORY_PROPOSAL_SCHEMA,
                    temperature=0.2,
                )
                output_dict = self._gen_service.generate_typed(request, CategoryProposalOutput)
                parsed: CategoryProposalOutput = output_dict["parsed"]
                if parsed.categories:
                    return [
                        AssessmentCategory(
                            id=f"cat-{_slugify(item.name)}",
                            name=item.name,
                            description=item.description,
                            evaluation_question=item.evaluation_question,
                            enabled=True,
                            is_ai_suggested=True,
                        )
                        for item in parsed.categories
                    ]
            except Exception:
                # Bounded fallback to deterministic categories
                pass

        return self._deterministic_fallback_categories(stripped_obj)

    @staticmethod
    def _deterministic_fallback_categories(objective: str) -> list[AssessmentCategory]:
        """Deterministic heuristic proposal when no live provider is used."""
        lower_obj = objective.lower()
        if "scholarship" in lower_obj or "grant" in lower_obj or "fellowship" in lower_obj:
            return [
                AssessmentCategory(
                    id="cat-eligibility-criteria",
                    name="Eligibility Criteria",
                    description="Requirements regarding enrollment, academic marks, and demographic qualifications.",
                    evaluation_question="What are the specific eligibility and qualifying criteria stated across sources?",
                    enabled=True,
                    is_ai_suggested=True,
                ),
                AssessmentCategory(
                    id="cat-financial-benefits",
                    name="Financial Benefits & Value",
                    description="Award amounts, disbursement schedules, and covered expenditures.",
                    evaluation_question="What financial grant amounts and benefits are provided?",
                    enabled=True,
                    is_ai_suggested=True,
                ),
                AssessmentCategory(
                    id="cat-deadlines-and-timeline",
                    name="Deadlines & Important Dates",
                    description="Application opening, submission deadlines, and key process milestones.",
                    evaluation_question="What are the key deadlines and do sources agree on the final cutoff date?",
                    enabled=True,
                    is_ai_suggested=True,
                ),
                AssessmentCategory(
                    id="cat-renewal-and-obligations",
                    name="Renewal & Maintenance Terms",
                    description="Ongoing academic or performance obligations required to maintain funding.",
                    evaluation_question="What criteria or conditions are required to renew the award in future cycles?",
                    enabled=True,
                    is_ai_suggested=True,
                ),
            ]
        else:
            return [
                AssessmentCategory(
                    id="cat-core-claims",
                    name="Core Claims & Scope",
                    description="Primary substantive propositions made regarding the subject.",
                    evaluation_question="What are the central factual claims asserted by available sources?",
                    enabled=True,
                    is_ai_suggested=True,
                ),
                AssessmentCategory(
                    id="cat-source-consistency",
                    name="Consistency & Contradictions",
                    description="Cross-source agreement and potential discrepancies on key parameters.",
                    evaluation_question="Where do sources agree or present conflicting data points?",
                    enabled=True,
                    is_ai_suggested=True,
                ),
                AssessmentCategory(
                    id="cat-evidence-currency",
                    name="Information Currency & Dates",
                    description="Timeliness of information relative to current operational cycles.",
                    evaluation_question="Which sources provide current cycle information versus outdated guidance?",
                    enabled=True,
                    is_ai_suggested=True,
                ),
                AssessmentCategory(
                    id="cat-information-gaps",
                    name="Unanswered Questions & Gaps",
                    description="Critical aspects omitted or unanswered by available documentation.",
                    evaluation_question="What essential questions remain unanswered by the ingested source set?",
                    enabled=True,
                    is_ai_suggested=True,
                ),
            ]
