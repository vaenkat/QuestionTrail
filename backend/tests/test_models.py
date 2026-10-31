"""Unit tests for domain-neutral evidence models and referential integrity."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from questiontrail.domain.models import (
    SourceType,
    SourceAuthority,
    ExtractionStatus,
    LocationType,
    AssessmentStatus,
    FindingType,
    FindingLabel,
    FindingSeverity,
    EvidenceRef,
    Source,
    Claim,
    AssessmentCategory,
    CategoryAssessment,
    Finding,
    VerificationAction,
    ResearchProject,
    AnalysisResult,
    AnalysisSnapshot,
    utc_now,
)


def make_valid_source(source_id: str = "src-01") -> Source:
    return Source(
        id=source_id,
        title="Official Portal Document",
        url="https://example.org/announcement",
        type=SourceType.webpage,
        authority=SourceAuthority.primary_official,
        publication_date="2026-08-14",
        cycle_or_version="2026-27",
        retrieved_at=datetime(2026, 8, 15, 10, 0, 0, tzinfo=timezone.utc),
        extraction_status=ExtractionStatus.success,
        content_hash="abc123sha256hash",
        raw_content="Official guidelines for the program."
    )


def make_valid_evidence_ref(source_id: str = "src-01") -> EvidenceRef:
    return EvidenceRef(
        source_id=source_id,
        exact_snippet="Candidates must submit verified records by October 5.",
        location_type=LocationType.section,
        location_value="Section 3.1: Deadlines",
        char_offset_start=100,
        char_offset_end=154,
        page_number=1
    )


class TestEvidenceRef:
    def test_valid_evidence_ref(self):
        ref = make_valid_evidence_ref()
        assert ref.source_id == "src-01"
        assert "October 5" in ref.exact_snippet
        assert ref.page_number == 1

    def test_rejects_empty_snippet(self):
        with pytest.raises(ValidationError):
            EvidenceRef(
                source_id="src-01",
                exact_snippet="",
                location_type=LocationType.page,
                location_value="p. 1"
            )

    def test_rejects_inverted_offsets(self):
        with pytest.raises(ValidationError, match="char_offset_start must not exceed char_offset_end"):
            EvidenceRef(
                source_id="src-01",
                exact_snippet="snippet",
                location_type=LocationType.char_offset,
                location_value="offset 20-10",
                char_offset_start=20,
                char_offset_end=10
            )


class TestSource:
    def test_valid_source_defaults_and_timezone(self):
        source = Source(
            id="src-02",
            title="Third Party Review",
            url="https://example.com/listing"
        )
        assert source.authority == SourceAuthority.third_party
        assert source.retrieved_at.tzinfo is not None
        assert source.type == SourceType.webpage
        assert source.publication_date is None

    def test_timezone_naive_datetime_converted_to_utc(self):
        naive_dt = datetime(2026, 9, 1, 12, 0, 0)
        source = Source(
            id="src-03",
            title="Document",
            retrieved_at=naive_dt
        )
        assert source.retrieved_at.tzinfo == timezone.utc


class TestFindingValidation:
    def test_information_gap_requires_sources_or_scope(self):
        # Fails when neither sources_examined nor scope_examined is given
        with pytest.raises(ValidationError, match="must state examined sources or scope"):
            Finding(
                id="f-01",
                type=FindingType.information_gap,
                rationale="No criteria found."
            )

        # Passes when scope_examined is provided
        f_with_scope = Finding(
            id="f-01",
            type=FindingType.information_gap,
            scope_examined="renewal_criteria",
            rationale="No statement on renewal requirements exists in available sources."
        )
        assert f_with_scope.label == FindingLabel.potential

        # Passes when sources_examined is provided
        f_with_sources = Finding(
            id="f-02",
            type=FindingType.information_gap,
            sources_examined=["src-01"],
            rationale="Examined official announcement but found no mention of renewal conditions."
        )
        assert "src-01" in f_with_sources.sources_examined

    def test_potential_conflict_requires_evidence_or_contrasting_claims(self):
        with pytest.raises(ValidationError, match="must cite evidence or contrasting claims"):
            Finding(
                id="f-03",
                type=FindingType.potential_conflict,
                rationale="Dates conflict."
            )

        f_valid = Finding(
            id="f-03",
            type=FindingType.potential_conflict,
            contrasting_claim_ids=["claim-01", "claim-02"],
            rationale="Source 1 states October 5 while Source 2 states September 30."
        )
        assert f_valid.label == FindingLabel.potential


class TestVerificationAction:
    def test_priority_score_bounds(self):
        # Valid score
        act = VerificationAction(
            id="act-01",
            priority_score=0.85,
            action="Check official portal FAQ",
            rationale="Resolve deadline discrepancy."
        )
        assert act.priority_score == 0.85

        # Score < 0.0 rejected
        with pytest.raises(ValidationError):
            VerificationAction(
                id="act-02",
                priority_score=-0.1,
                action="Verify",
                rationale="Test"
            )

        # Score > 1.0 rejected
        with pytest.raises(ValidationError):
            VerificationAction(
                id="act-03",
                priority_score=1.1,
                action="Verify",
                rationale="Test"
            )


class TestReferentialIntegrity:
    @pytest.fixture
    def valid_bundle_data(self):
        source = make_valid_source("src-01")
        evidence = make_valid_evidence_ref("src-01")
        
        claim1 = Claim(
            id="c-01",
            normalized_statement="Application deadline is October 5, 2026.",
            evidence_refs=[evidence],
            is_verified=True
        )
        
        claim2 = Claim(
            id="c-02",
            normalized_statement="Application deadline is September 30, 2026.",
            evidence_refs=[evidence],
            is_verified=False
        )

        category = AssessmentCategory(
            id="cat-01",
            name="Key Deadlines",
            description="Timeline and submission dates",
            evaluation_question="What is the final submission cutoff?",
            is_ai_suggested=False
        )

        assessment = CategoryAssessment(
            category_id="cat-01",
            status=AssessmentStatus.conflicting,
            supporting_claim_ids=["c-01"],
            contrary_claim_ids=["c-02"],
            rationale="Third party source indicates September 30 cutoff."
        )

        finding = Finding(
            id="f-01",
            type=FindingType.potential_conflict,
            label=FindingLabel.potential,
            severity=FindingSeverity.high,
            rationale="Candidate sources assert different closing dates.",
            contrasting_claim_ids=["c-01", "c-02"],
            evidence_refs=[evidence]
        )

        action = VerificationAction(
            id="act-01",
            priority_score=0.9,
            action="Verify latest announcement on official website",
            rationale="Resolve candidate deadline ambiguity",
            linked_claim_ids=["c-01", "c-02"],
            linked_finding_ids=["f-01"]
        )

        return {
            "project_id": "proj-01",
            "dataset_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "sources": [source],
            "claims": [claim1, claim2],
            "assessments": [assessment],
            "findings": [finding],
            "actions": [action]
        }

    def test_valid_bundle_passes(self, valid_bundle_data):
        result = AnalysisResult(**valid_bundle_data)
        assert result.project_id == "proj-01"
        assert len(result.claims) == 2
        assert len(result.findings) == 1

        # Test snapshot packaging
        snapshot = AnalysisSnapshot(
            dataset_hash=result.dataset_hash,
            schema_version="1.0.0",
            provider="mock",
            model="mock-deterministic",
            payload=result
        )
        assert snapshot.dataset_hash == result.dataset_hash
        assert snapshot.payload.project_id == "proj-01"

    def test_rejects_claim_with_unknown_source_id(self, valid_bundle_data):
        # Modify claim to reference unknown source
        orphan_evidence = EvidenceRef(
            source_id="nonexistent-source-id",
            exact_snippet="Fake snippet",
            location_type=LocationType.page,
            location_value="Page 1"
        )
        valid_bundle_data["claims"][0].evidence_refs = [orphan_evidence]

        with pytest.raises(ValidationError, match="references unknown source_id 'nonexistent-source-id'"):
            AnalysisResult(**valid_bundle_data)

    def test_rejects_finding_with_unknown_source_id(self, valid_bundle_data):
        orphan_evidence = EvidenceRef(
            source_id="nonexistent-source-id",
            exact_snippet="Fake snippet",
            location_type=LocationType.page,
            location_value="Page 1"
        )
        valid_bundle_data["findings"][0].evidence_refs = [orphan_evidence]

        with pytest.raises(ValidationError, match="references unknown source_id 'nonexistent-source-id'"):
            AnalysisResult(**valid_bundle_data)

    def test_rejects_finding_with_unknown_contrasting_claim(self, valid_bundle_data):
        valid_bundle_data["findings"][0].contrasting_claim_ids = ["c-01", "unknown-claim-id"]

        with pytest.raises(ValidationError, match="lists unknown contrasting_claim_id 'unknown-claim-id'"):
            AnalysisResult(**valid_bundle_data)

    def test_rejects_assessment_with_unknown_supporting_claim(self, valid_bundle_data):
        valid_bundle_data["assessments"][0].supporting_claim_ids = ["unknown-claim-id"]

        with pytest.raises(ValidationError, match="references unknown supporting claim 'unknown-claim-id'"):
            AnalysisResult(**valid_bundle_data)

    def test_rejects_action_with_unknown_linked_finding(self, valid_bundle_data):
        valid_bundle_data["actions"][0].linked_finding_ids = ["unknown-finding-id"]

        with pytest.raises(ValidationError, match="references unknown finding_id 'unknown-finding-id'"):
            AnalysisResult(**valid_bundle_data)


class TestDomainNeutrality:
    """Verify that models contain no scholarship-specific or narrow domain attributes."""

    FORBIDDEN_DOMAIN_TERMS = [
        "scholarship",
        "stipend",
        "bursary",
        "tuition",
        "caste",
        "income_certificate",
        "reliance",
        "ug_scholarship"
    ]

    def test_model_fields_are_domain_neutral(self):
        models = [
            EvidenceRef,
            Source,
            Claim,
            AssessmentCategory,
            CategoryAssessment,
            Finding,
            VerificationAction,
            ResearchProject,
            AnalysisResult,
            AnalysisSnapshot,
        ]

        for model in models:
            for field_name in model.model_fields.keys():
                for term in self.FORBIDDEN_DOMAIN_TERMS:
                    assert term not in field_name.lower(), (
                        f"Model {model.__name__} has domain-specific field: {field_name}"
                    )
