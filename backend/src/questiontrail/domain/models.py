"""Domain models for QuestionTrail evidence-first research workspace."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class SourceType(str, Enum):
    """Generic source mediums."""
    webpage = "webpage"
    document = "document"
    pdf = "pdf"
    api = "api"
    manual = "manual"


class SourceAuthority(str, Enum):
    """Authority ranking of an ingested source."""
    primary_official = "primary_official"
    secondary_authoritative = "secondary_authoritative"
    third_party = "third_party"
    unknown = "unknown"


ANALYSIS_SCHEMA_VERSION = "1.0.0"


class ExtractionStatus(str, Enum):
    """Status of content or claim extraction."""
    pending = "pending"
    success = "success"
    partial = "partial"
    failed = "failed"


class LocationType(str, Enum):
    """Location reference types within source content."""
    page = "page"
    section = "section"
    paragraph = "paragraph"
    xpath = "xpath"
    char_offset = "char_offset"
    url = "url"


class AssessmentStatus(str, Enum):
    """Status of category evidence coverage."""
    supported = "supported"
    partially_covered = "partially_covered"
    conflicting = "conflicting"
    unsupported = "unsupported"
    requires_verification = "requires_verification"


class FindingType(str, Enum):
    """Taxonomy of analytical findings."""
    potential_conflict = "potential_conflict"
    dated_information = "dated_information"
    information_gap = "information_gap"
    unsupported_assertion = "unsupported_assertion"
    consistency_signal = "consistency_signal"


class FindingLabel(str, Enum):
    """Epistemic label for a finding to prevent treating AI signals as confirmed facts."""
    potential = "potential"
    confirmed = "confirmed"


class FindingSeverity(str, Enum):
    """Actionable urgency of a finding."""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class EvidenceRef(BaseModel):
    """Verbatim citation pointing directly to an exact snippet within a known source."""
    source_id: str = Field(..., min_length=1, description="Identifier of the source containing this evidence")
    exact_snippet: str = Field(..., min_length=1, description="Verbatim text extracted from the source")
    location_type: LocationType = Field(default=LocationType.section, description="Type of document locator")
    location_value: str = Field(..., min_length=1, description="Human-readable location identifier (e.g. Page 3, Section 2.1)")
    char_offset_start: int | None = Field(default=None, ge=0)
    char_offset_end: int | None = Field(default=None, ge=0)
    page_number: int | None = Field(default=None, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_offsets(self) -> "EvidenceRef":
        if self.char_offset_start is not None and self.char_offset_end is not None:
            if self.char_offset_start > self.char_offset_end:
                raise ValueError("char_offset_start must not exceed char_offset_end")
        return self


class Source(BaseModel):
    """Generic information source with provenance metadata."""
    id: str = Field(..., min_length=1, description="Unique source identifier")
    title: str = Field(..., min_length=1, description="Title of the source")
    url: str | None = Field(default=None, description="Original public or canonical URL")
    type: SourceType = Field(default=SourceType.webpage, description="Medium of source")
    authority: SourceAuthority = Field(default=SourceAuthority.third_party, description="Assessed source authority")
    publication_date: str | None = Field(default=None, description="Optional publication date in ISO format or cycle date string")
    cycle_or_version: str | None = Field(default=None, description="Optional version or active cycle identifier")
    retrieved_at: datetime = Field(default_factory=utc_now, description="Timezone-aware timestamp of ingestion")
    extraction_status: ExtractionStatus = Field(default=ExtractionStatus.success)
    content_hash: str | None = Field(default=None, description="Deterministic hash (e.g. SHA-256) of raw extracted text")
    raw_content: str | None = Field(default=None, description="Extracted raw text content")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("retrieved_at")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class Claim(BaseModel):
    """Atomic normalized statement derived from and linked to verifiable evidence."""
    id: str = Field(..., min_length=1)
    normalized_statement: str = Field(..., min_length=1, description="Clear, verifiable proposition")
    entities: list[str] = Field(default_factory=list, description="Key named entities involved in statement")
    dates: list[str] = Field(default_factory=list, description="Extracted dates mentioned in claim")
    evidence_refs: list[EvidenceRef] = Field(
        default_factory=list,
        description="Source evidence references directly establishing this claim"
    )
    extraction_status: ExtractionStatus = Field(default=ExtractionStatus.success)
    is_verified: bool = Field(
        default=False, 
        description="Whether this claim has been validated as a sourced fact rather than an unverified assertion"
    )


class AssessmentCategory(BaseModel):
    """Evaluation dimension within a research objective."""
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    evaluation_question: str = Field(..., min_length=1)
    enabled: bool = Field(default=True)
    is_ai_suggested: bool = Field(
        default=False,
        description="Indicates an AI-proposed category requiring user acceptance"
    )


class CategoryAssessment(BaseModel):
    """Coverage and consistency assessment of a category across project sources."""
    category_id: str = Field(..., min_length=1)
    status: AssessmentStatus = Field(default=AssessmentStatus.requires_verification)
    supporting_claim_ids: list[str] = Field(default_factory=list)
    contrary_claim_ids: list[str] = Field(default_factory=list)
    unanswered_questions: list[str] = Field(default_factory=list)
    rationale: str | None = Field(default=None)


class Finding(BaseModel):
    """Analytical signal or gap identified during evaluation."""
    id: str = Field(..., min_length=1)
    type: FindingType
    label: FindingLabel = Field(
        default=FindingLabel.potential,
        description="Must be 'potential' until user confirms, preventing unwarranted assertions"
    )
    severity: FindingSeverity = Field(default=FindingSeverity.medium)
    rationale: str = Field(..., min_length=1, description="Explanation of why this finding was flagged")
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    
    # Missing information and scope representation:
    sources_examined: list[str] = Field(
        default_factory=list,
        description="Identifiers of sources searched when identifying missing information or gaps"
    )
    scope_examined: str | None = Field(
        default=None,
        description="Category ID or topic scope that was evaluated and found lacking"
    )
    contrasting_claim_ids: list[str] = Field(
        default_factory=list,
        description="Claims illustrating tension or contradiction in conflict findings"
    )

    @model_validator(mode="after")
    def validate_finding_structure(self) -> "Finding":
        # For information gaps, require either examined sources or explicit scope
        if self.type == FindingType.information_gap:
            if not self.sources_examined and not self.scope_examined:
                raise ValueError("information_gap findings must state examined sources or scope")
        # For conflict findings, recommend or require evidence or contrasting claims
        if self.type == FindingType.potential_conflict:
            if not self.evidence_refs and not self.contrasting_claim_ids:
                raise ValueError("potential_conflict findings must cite evidence or contrasting claims")
        return self


class VerificationAction(BaseModel):
    """Deterministic, prioritized recommendation for resolving uncertainty or conflict."""
    id: str = Field(..., min_length=1)
    priority_score: float = Field(..., ge=0.0, le=1.0, description="Normalized deterministic priority score")
    action: str = Field(..., min_length=1, description="Concrete step to verify information")
    rationale: str = Field(..., min_length=1, description="Why this action is recommended")
    recommended_source: str | None = Field(default=None, description="Primary authority or URL recommended to check")
    linked_claim_ids: list[str] = Field(default_factory=list)
    linked_finding_ids: list[str] = Field(default_factory=list)


class ResearchProject(BaseModel):
    """Top-level research project definition."""
    id: str = Field(..., min_length=1)
    objective: str = Field(..., min_length=1)
    categories: list[AssessmentCategory] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    dataset_hash: str | None = Field(default=None)
    analysis_schema_version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("created_at", "updated_at")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class AnalysisResult(BaseModel):
    """Assembled analytical output bundle with full referential integrity checks."""
    project_id: str = Field(..., min_length=1)
    dataset_hash: str = Field(..., min_length=1, description="Canonical hash of the analyzed source corpus")
    analysis_schema_version: str = Field(default="1.0.0")
    sources: list[Source] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    assessments: list[CategoryAssessment] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    actions: list[VerificationAction] = Field(default_factory=list)
    summary: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_referential_integrity(self) -> "AnalysisResult":
        """Verify that every reference points to a known source, claim, or finding in this bundle."""
        source_id_set = {s.id for s in self.sources}
        claim_id_set = {c.id for c in self.claims}
        finding_id_set = {f.id for f in self.findings}

        # 1. Every EvidenceRef in claims must reference a known source in self.sources
        for claim in self.claims:
            for ref in claim.evidence_refs:
                if source_id_set and ref.source_id not in source_id_set:
                    raise ValueError(
                        f"Claim '{claim.id}' references unknown source_id '{ref.source_id}'"
                    )

        # 2. Every EvidenceRef in findings must reference a known source in self.sources
        for finding in self.findings:
            for ref in finding.evidence_refs:
                if source_id_set and ref.source_id not in source_id_set:
                    raise ValueError(
                        f"Finding '{finding.id}' references unknown source_id '{ref.source_id}'"
                    )
            # Sources examined must also be valid sources if sources are provided
            for src_id in finding.sources_examined:
                if source_id_set and src_id not in source_id_set:
                    raise ValueError(
                        f"Finding '{finding.id}' lists unknown sources_examined id '{src_id}'"
                    )
            # Contrasting claims must exist
            for c_id in finding.contrasting_claim_ids:
                if claim_id_set and c_id not in claim_id_set:
                    raise ValueError(
                        f"Finding '{finding.id}' lists unknown contrasting_claim_id '{c_id}'"
                    )

        # 3. Category assessments must reference known claims
        for assessment in self.assessments:
            for c_id in assessment.supporting_claim_ids:
                if claim_id_set and c_id not in claim_id_set:
                    raise ValueError(
                        f"Assessment for category '{assessment.category_id}' references unknown supporting claim '{c_id}'"
                    )
            for c_id in assessment.contrary_claim_ids:
                if claim_id_set and c_id not in claim_id_set:
                    raise ValueError(
                        f"Assessment for category '{assessment.category_id}' references unknown contrary claim '{c_id}'"
                    )

        # 4. Verification actions must reference known claims and findings
        for action in self.actions:
            for c_id in action.linked_claim_ids:
                if claim_id_set and c_id not in claim_id_set:
                    raise ValueError(
                        f"VerificationAction '{action.id}' references unknown claim_id '{c_id}'"
                    )
            for f_id in action.linked_finding_ids:
                if finding_id_set and f_id not in finding_id_set:
                    raise ValueError(
                        f"VerificationAction '{action.id}' references unknown finding_id '{f_id}'"
                    )

        return self


class AnalysisSnapshot(BaseModel):
    """Content-addressed snapshot of analysis result eligible for exact cache match."""
    dataset_hash: str = Field(..., min_length=1, description="SHA-256 hash of canonical source set")
    schema_version: str = Field(..., min_length=1, description="Schema version of analysis payload")
    provider: str = Field(..., min_length=1, description="Provider used (e.g. nvidia, gemini, mock, precomputed)")
    model: str = Field(..., min_length=1, description="Model identifier used to produce snapshot")
    payload: AnalysisResult = Field(..., description="Full verified analytical result bundle")
    created_at: datetime = Field(default_factory=utc_now)
