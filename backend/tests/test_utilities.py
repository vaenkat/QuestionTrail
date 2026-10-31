"""Comprehensive unit tests for deterministic services (canonical, cache_safety, dates)."""

from datetime import date, datetime, timedelta, timezone
import pytest

from questiontrail.domain.models import (
    AssessmentCategory,
    Source,
    SourceType,
    SourceAuthority,
    AnalysisSnapshot,
    AnalysisResult,
)
from questiontrail.services.canonical import (
    canonical_json,
    sha256_hex,
    compute_content_hash,
    compute_dataset_hash,
)
from questiontrail.services.cache_safety import (
    check_snapshot_eligibility,
    is_snapshot_eligible,
)
from questiontrail.services.dates import (
    FreshnessStatus,
    classify_freshness,
    parse_date_safe,
    normalize_to_utc,
)


# --- 1. Canonical JSON & SHA-256 Tests ---

class TestCanonicalSerialization:
    def test_canonical_json_sorts_keys_deterministically(self):
        dict_a = {"z": 1, "a": 2, "m": {"b": 3, "a": 4}}
        dict_b = {"a": 2, "z": 1, "m": {"a": 4, "b": 3}}
        assert canonical_json(dict_a) == canonical_json(dict_b)
        assert canonical_json(dict_a) == '{"a":2,"m":{"a":4,"b":3},"z":1}'

    def test_canonical_json_preserves_array_sequence_order(self):
        list_a = [1, 3, 2]
        list_b = [1, 2, 3]
        # Array ordering must be preserved, NOT automatically sorted
        assert canonical_json(list_a) != canonical_json(list_b)
        assert canonical_json(list_a) == "[1,3,2]"

    def test_canonical_json_normalizes_datetimes(self):
        dt_utc = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)
        # Indian Standard Time (+05:30) at 17:30 is the exact same UTC instant
        dt_ist = datetime(2026, 10, 31, 17, 30, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))

        payload_utc = {"timestamp": dt_utc}
        payload_ist = {"timestamp": dt_ist}

        assert canonical_json(payload_utc) == canonical_json(payload_ist)
        assert canonical_json(payload_utc) == '{"timestamp":"2026-10-31T12:00:00+00:00"}'

    def test_sha256_determinism(self):
        h1 = sha256_hex("QuestionTrail deterministic verification")
        h2 = sha256_hex("QuestionTrail deterministic verification")
        assert h1 == h2
        assert len(h1) == 64

    def test_compute_content_hash_normalizes_line_endings(self):
        text_crlf = "Line 1\r\nLine 2\r\n"
        text_lf = "Line 1\nLine 2\n"
        assert compute_content_hash(text_crlf) == compute_content_hash(text_lf)


# --- 2. Dataset Hashing & Invalidation Tests ---

class TestDatasetHashing:
    @pytest.fixture
    def sample_sources(self):
        return [
            Source(
                id="src-01",
                title="Official Portal",
                url="https://example.org/source1",
                type=SourceType.webpage,
                authority=SourceAuthority.primary_official,
                publication_date="2026-08-14",
                cycle_or_version="2026-27",
                retrieved_at=datetime(2026, 8, 15, 10, 0, 0, tzinfo=timezone.utc),
                content_hash="hash-source-1"
            ),
            Source(
                id="src-02",
                title="Reference Media",
                url="https://example.org/source2",
                type=SourceType.webpage,
                authority=SourceAuthority.secondary_authoritative,
                publication_date="2026-09-01",
                cycle_or_version="2026-27",
                retrieved_at=datetime(2026, 9, 2, 10, 0, 0, tzinfo=timezone.utc),
                content_hash="hash-source-2"
            )
        ]

    @pytest.fixture
    def sample_categories(self):
        return [
            AssessmentCategory(
                id="cat-01",
                name="Eligibility",
                description="Evaluation of academic qualifications",
                evaluation_question="What are the minimum requirements?"
            ),
            AssessmentCategory(
                id="cat-02",
                name="Deadlines",
                description="Key application dates",
                evaluation_question="What is the final closing date?"
            )
        ]

    def test_dataset_hash_is_invariant_to_source_list_order(self, sample_sources):
        # Order: [src-01, src-02] vs [src-02, src-01]
        hash_order_1 = compute_dataset_hash(sample_sources)
        hash_order_2 = compute_dataset_hash([sample_sources[1], sample_sources[0]])
        assert hash_order_1 == hash_order_2

    def test_dataset_hash_ignores_volatile_retrieval_timestamp(self, sample_sources):
        hash_initial = compute_dataset_hash(sample_sources)

        # Change volatile retrieved_at on src-01
        sample_sources[0].retrieved_at = datetime(2026, 10, 31, 22, 0, 0, tzinfo=timezone.utc)
        hash_updated_retrieval = compute_dataset_hash(sample_sources)

        # Volatile timing must NOT invalidate analytical hash
        assert hash_initial == hash_updated_retrieval

    def test_content_modification_changes_dataset_hash(self, sample_sources):
        hash_initial = compute_dataset_hash(sample_sources)

        # Alter content_hash of src-02
        sample_sources[1].content_hash = "modified-hash-source-2"
        hash_modified = compute_dataset_hash(sample_sources)

        assert hash_initial != hash_modified

    def test_objective_modification_changes_dataset_hash(self, sample_sources):
        obj1 = "Assess consistency and currency of application deadlines."
        obj2 = "Assess eligibility criteria and renewal terms."

        hash_obj1 = compute_dataset_hash(sample_sources, objective=obj1)
        hash_obj2 = compute_dataset_hash(sample_sources, objective=obj2)

        assert hash_obj1 != hash_obj2

    def test_category_modification_changes_dataset_hash(self, sample_sources, sample_categories):
        hash_cat1 = compute_dataset_hash(sample_sources, categories=sample_categories)

        # Disable one category
        sample_categories[0].enabled = False
        hash_cat_disabled = compute_dataset_hash(sample_sources, categories=sample_categories)

        assert hash_cat1 != hash_cat_disabled


# --- 3. Cache Safety & Snapshot Eligibility Tests ---

class TestCacheSafety:
    def test_exact_cache_match_is_accepted(self):
        target_hash = "abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        snapshot = {
            "dataset_hash": target_hash,
            "schema_version": "1.0.0",
            "provider": "mock",
            "model": "mock-model"
        }

        result = check_snapshot_eligibility(snapshot, expected_dataset_hash=target_hash, expected_schema_version="1.0.0")
        assert result.is_eligible is True
        assert result.dataset_hash_matched is True
        assert result.schema_version_matched is True
        assert is_snapshot_eligible(snapshot, target_hash, "1.0.0") is True

    def test_dataset_hash_mismatch_rejected(self):
        expected_hash = "hash-A"
        snapshot = {
            "dataset_hash": "hash-B-altered-corpus",
            "schema_version": "1.0.0"
        }

        result = check_snapshot_eligibility(snapshot, expected_dataset_hash=expected_hash, expected_schema_version="1.0.0")
        assert result.is_eligible is False
        assert result.dataset_hash_matched is False
        assert result.schema_version_matched is True
        assert "Dataset content mismatch" in result.reason

    def test_schema_version_mismatch_rejected(self):
        expected_hash = "hash-A"
        snapshot = {
            "dataset_hash": expected_hash,
            "schema_version": "2.0.0-incompatible"
        }

        result = check_snapshot_eligibility(snapshot, expected_dataset_hash=expected_hash, expected_schema_version="1.0.0")
        assert result.is_eligible is False
        assert result.dataset_hash_matched is True
        assert result.schema_version_matched is False
        assert "Schema version mismatch" in result.reason

    def test_both_hash_and_schema_mismatch_rejected(self):
        snapshot = {
            "dataset_hash": "wrong-hash",
            "schema_version": "0.9.0"
        }
        result = check_snapshot_eligibility(snapshot, expected_dataset_hash="target-hash", expected_schema_version="1.0.0")
        assert result.is_eligible is False
        assert result.dataset_hash_matched is False
        assert result.schema_version_matched is False


# --- 4. Date Parsing and Freshness Classification Tests ---

class TestDateAndFreshness:
    # Explicit reference date: 2026-10-31 12:00:00 UTC
    AS_OF = datetime(2026, 10, 31, 12, 0, 0, tzinfo=timezone.utc)

    def test_safe_date_parsing_various_formats(self):
        # ISO string with Z
        dt, valid = parse_date_safe("2026-08-14T10:00:00Z")
        assert valid is True
        assert dt == datetime(2026, 8, 14, 10, 0, 0, tzinfo=timezone.utc)

        # Simple date string YYYY-MM-DD
        dt2, valid2 = parse_date_safe("2026-08-14")
        assert valid2 is True
        assert dt2.year == 2026 and dt2.month == 8 and dt2.day == 14

        # Date object
        dt3, valid3 = parse_date_safe(date(2026, 9, 1))
        assert valid3 is True
        assert dt3 == datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc)

    def test_undated_source_handling(self):
        for val in (None, "", "   "):
            eval_result = classify_freshness(val, as_of=self.AS_OF)
            assert eval_result.status == FreshnessStatus.undated
            assert "does not provide a verifiable publication date" in (eval_result.warning_message or "")
            assert eval_result.age_days is None

    def test_invalid_date_handling(self):
        for bad_val in ("not-a-date", "2026-99-99", "random_string"):
            eval_result = classify_freshness(bad_val, as_of=self.AS_OF)
            assert eval_result.status == FreshnessStatus.invalid_date
            assert "malformed and could not be verified" in (eval_result.warning_message or "")

    def test_fresh_source_within_threshold(self):
        # 60 days before AS_OF (approx Aug 2026 relative to Oct 31 2026)
        pub_date = "2026-08-31"
        eval_result = classify_freshness(pub_date, as_of=self.AS_OF, max_age_days=365)
        assert eval_result.status == FreshnessStatus.fresh
        assert eval_result.warning_message is None
        assert eval_result.age_days == 61

    def test_stale_source_exceeding_threshold(self):
        # Older cycle FAQ: published in Aug 2024 (approx 800 days old)
        older_faq_date = "2024-08-14"
        eval_result = classify_freshness(older_faq_date, as_of=self.AS_OF, max_age_days=365)
        assert eval_result.status == FreshnessStatus.stale
        assert eval_result.age_days is not None and eval_result.age_days > 365
        assert "is 808 days old relative to research context" in (eval_result.warning_message or "")

    def test_fresh_stale_exact_boundary(self):
        # Exactly 365 days ago
        exact_365_days_ago = (self.AS_OF - timedelta(days=365)).strftime("%Y-%m-%d")
        eval_365 = classify_freshness(exact_365_days_ago, as_of=self.AS_OF, max_age_days=365)
        assert eval_365.status == FreshnessStatus.fresh
        assert eval_365.age_days == 365

        # 366 days ago (exceeds threshold)
        exact_366_days_ago = (self.AS_OF - timedelta(days=366)).strftime("%Y-%m-%d")
        eval_366 = classify_freshness(exact_366_days_ago, as_of=self.AS_OF, max_age_days=365)
        assert eval_366.status == FreshnessStatus.stale
        assert eval_366.age_days == 366

    def test_future_dated_source_flagged_for_review(self):
        # Future date: Nov 20, 2026 relative to Oct 31, 2026
        future_date = "2026-11-20"
        eval_result = classify_freshness(future_date, as_of=self.AS_OF)
        assert eval_result.status == FreshnessStatus.future_dated
        assert "is in the future" in (eval_result.warning_message or "")
        assert eval_result.age_days is not None and eval_result.age_days < 0

    def test_timezone_consistency(self):
        # Test comparing dates with different timezone representations
        utc_dt = datetime(2026, 10, 30, 20, 0, 0, tzinfo=timezone.utc)
        ist_dt = datetime(2026, 10, 31, 1, 30, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))

        # Both represent the exact same UTC instant
        res_utc = classify_freshness(utc_dt, as_of=self.AS_OF)
        res_ist = classify_freshness(ist_dt, as_of=self.AS_OF)

        assert res_utc.status == res_ist.status
        assert res_utc.age_days == res_ist.age_days
