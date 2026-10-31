"""Tests for the curated scholarship demonstration corpus."""

from questiontrail.data.scholarship_corpus import (
    DEMO_OBJECTIVE,
    SOURCE_TEXTS,
    get_curated_sources,
    get_curated_categories,
    get_curated_analysis_result,
    get_curated_snapshot,
)
from questiontrail.services.canonical import compute_dataset_hash, compute_content_hash
from questiontrail.services.cache_safety import check_snapshot_eligibility
from questiontrail.domain.models import ANALYSIS_SCHEMA_VERSION


def test_sources_count_and_hashes():
    sources = get_curated_sources()
    assert len(sources) == 5
    for s in sources:
        assert s.id in SOURCE_TEXTS
        assert s.content_hash == compute_content_hash(SOURCE_TEXTS[s.id])
        assert s.url.startswith("https://")
        assert s.publication_date is not None


def test_curated_categories():
    cats = get_curated_categories()
    assert len(cats) >= 4
    for c in cats:
        assert c.id.startswith("cat-")
        assert len(c.name) > 0
        assert len(c.evaluation_question) > 0
        assert c.enabled is True


def test_analysis_result_referential_integrity():
    result = get_curated_analysis_result()
    assert result.project_id == "proj-scholarship-curated"
    assert len(result.claims) > 0
    assert len(result.assessments) == len(get_curated_categories())
    assert len(result.findings) >= 3
    assert len(result.actions) >= 3

    # All claim evidence references point to valid sources
    source_ids = {s.id for s in result.sources}
    for claim in result.claims:
        for ref in claim.evidence_refs:
            assert ref.source_id in source_ids
            # Exact snippet must exist in source text
            assert ref.exact_snippet in SOURCE_TEXTS[ref.source_id]


def test_curated_snapshot_is_cache_eligible():
    snapshot = get_curated_snapshot()
    sources = get_curated_sources()
    categories = get_curated_categories()

    computed_hash = compute_dataset_hash(
        sources=sources,
        objective=DEMO_OBJECTIVE,
        categories=categories,
    )
    assert snapshot.dataset_hash == computed_hash
    assert snapshot.schema_version == ANALYSIS_SCHEMA_VERSION

    # Test cache safety check
    res = check_snapshot_eligibility(
        snapshot=snapshot,
        expected_dataset_hash=computed_hash,
        expected_schema_version=ANALYSIS_SCHEMA_VERSION,
    )
    assert res.is_eligible is True
    assert res.dataset_hash_matched is True
    assert res.schema_version_matched is True


def test_cache_safety_fails_on_tampered_source():
    snapshot = get_curated_snapshot()
    sources = get_curated_sources()
    # Tamper with one source's content hash
    sources[0].content_hash = "tampered_hash_value"
    categories = get_curated_categories()

    tampered_hash = compute_dataset_hash(
        sources=sources,
        objective=DEMO_OBJECTIVE,
        categories=categories,
    )
    res = check_snapshot_eligibility(
        snapshot=snapshot,
        expected_dataset_hash=tampered_hash,
        expected_schema_version=ANALYSIS_SCHEMA_VERSION,
    )
    assert res.is_eligible is False
    assert res.dataset_hash_matched is False
    assert "Dataset content mismatch" in res.reason
