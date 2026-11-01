"""QuestionTrail services package."""

from questiontrail.services.canonical import (
    canonical_json,
    sha256_hex,
    compute_content_hash,
    compute_dataset_hash,
    extract_source_canonical_dict,
)
from questiontrail.services.cache_safety import (
    check_snapshot_eligibility,
    is_snapshot_eligible,
    CacheEligibilityResult,
)
from questiontrail.services.dates import (
    FreshnessStatus,
    FreshnessEvaluation,
    parse_date_safe,
    classify_freshness,
    normalize_to_utc,
)
from questiontrail.services.url_ingestion import (
    fetch_and_extract_url,
    validate_url_safety,
    IngestionError,
)
from questiontrail.services.pdf_ingestion import (
    extract_pdf_source,
)

__all__ = [
    "canonical_json",
    "sha256_hex",
    "compute_content_hash",
    "compute_dataset_hash",
    "extract_source_canonical_dict",
    "check_snapshot_eligibility",
    "is_snapshot_eligible",
    "CacheEligibilityResult",
    "FreshnessStatus",
    "FreshnessEvaluation",
    "parse_date_safe",
    "classify_freshness",
    "normalize_to_utc",
    "fetch_and_extract_url",
    "validate_url_safety",
    "extract_pdf_source",
    "IngestionError",
]
