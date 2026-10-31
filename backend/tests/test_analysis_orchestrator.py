"""Tests for AnalysisOrchestrator."""

from datetime import datetime, timezone
import pytest

from questiontrail.services.analysis_orchestrator import AnalysisOrchestrator
from questiontrail.data.scholarship_corpus import (
    get_curated_sources,
    get_curated_categories,
    DEMO_OBJECTIVE,
)
from questiontrail.domain.models import (
    Source,
    SourceAuthority,
    SourceType,
    AssessmentCategory,
    FindingType,
)


def test_rejects_empty_sources_or_categories():
    orchestrator = AnalysisOrchestrator()
    cats = get_curated_categories()
    sources = get_curated_sources()

    with pytest.raises(ValueError, match="zero sources"):
        orchestrator.analyze_project("proj-1", "Obj", [], cats)

    with pytest.raises(ValueError, match="zero evaluation categories"):
        orchestrator.analyze_project("proj-1", "Obj", sources, [])


def test_curated_dataset_returns_precomputed_mode():
    orchestrator = AnalysisOrchestrator()
    sources = get_curated_sources()
    cats = get_curated_categories()

    result, mode = orchestrator.analyze_project(
        project_id="proj-curated-test",
        objective=DEMO_OBJECTIVE,
        sources=sources,
        categories=cats,
    )

    assert mode == "precomputed"
    assert len(result.claims) >= 7
    assert len(result.findings) >= 3
    assert len(result.actions) >= 3
    # Check that known findings exist in the precomputed baseline
    finding_types = {f.type for f in result.findings}
    assert FindingType.potential_conflict in finding_types
    assert FindingType.dated_information in finding_types
    assert FindingType.information_gap in finding_types


def test_dynamic_analysis_identifies_stale_source_and_gap():
    orchestrator = AnalysisOrchestrator()
    as_of = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)

    # 1 fresh source, 1 intentionally stale source (published 2024)
    sources = [
        Source(
            id="src-fresh-policy",
            title="Current Environmental Regulations 2026",
            url="https://example.gov/env-2026",
            type=SourceType.webpage,
            authority=SourceAuthority.primary_official,
            publication_date="2026-05-01",
            raw_content="Industrial emissions must not exceed 50 ppm particulate matter under current 2026 rules.",
        ),
        Source(
            id="src-old-policy",
            title="Archived Environmental Guidelines 2023",
            url="https://example.gov/archive-2023",
            type=SourceType.webpage,
            authority=SourceAuthority.secondary_authoritative,
            publication_date="2023-01-15",
            raw_content="Emissions standard limit was 100 ppm particulate matter as of 2023.",
        ),
    ]

    categories = [
        AssessmentCategory(
            id="cat-emissions",
            name="Emissions Thresholds",
            description="Allowable industrial particulate matter emissions limits.",
            evaluation_question="What are the maximum particulate emissions limits?",
            enabled=True,
        ),
        AssessmentCategory(
            id="cat-penalties",
            name="Violation Penalties",
            description="Monetary fines and legal sanctions for exceeding limits.",
            evaluation_question="What specific financial penalties apply to non-compliant operators?",
            enabled=True,
        ),
    ]

    result, mode = orchestrator.analyze_project(
        project_id="proj-env-eval",
        objective="Assess industrial emissions regulations currency and enforcement",
        sources=sources,
        categories=categories,
        as_of=as_of,
    )

    assert mode in ("mock", "precomputed")
    assert result.project_id == "proj-env-eval"

    # Verify stale source triggered dated_information finding
    dated_findings = [f for f in result.findings if f.type == FindingType.dated_information]
    assert len(dated_findings) >= 1
    assert any("2023" in f.rationale for f in dated_findings)

    # Verify empty category triggered information_gap finding
    gap_findings = [f for f in result.findings if f.type == FindingType.information_gap]
    assert len(gap_findings) >= 1
    assert any("Violation Penalties" in (f.scope_examined or "") for f in gap_findings)

    # Actions must be sorted descending by priority_score
    scores = [a.priority_score for a in result.actions]
    assert scores == sorted(scores, reverse=True)


def test_cache_hit_on_subsequent_call():
    orchestrator = AnalysisOrchestrator()
    sources = [
        Source(
            id="src-unique-test",
            title="Test Source",
            raw_content="Some test content to evaluate caching behavior.",
        )
    ]
    categories = [
        AssessmentCategory(
            id="cat-test",
            name="Test Category",
            description="Test Description",
            evaluation_question="What is the test result?",
        )
    ]

    # First call -> dynamic execution and cached
    res1, mode1 = orchestrator.analyze_project("proj-cache", "Test objective", sources, categories)
    # Second call -> cache hit
    res2, mode2 = orchestrator.analyze_project("proj-cache", "Test objective", sources, categories)

    assert mode2 == "precomputed"
    assert res1.dataset_hash == res2.dataset_hash
