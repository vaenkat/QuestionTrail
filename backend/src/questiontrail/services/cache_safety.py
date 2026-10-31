"""Deterministic cache eligibility and safety guard."""

from typing import Any
from pydantic import BaseModel

from questiontrail.domain.models import AnalysisSnapshot


class CacheEligibilityResult(BaseModel):
    """Result of checking whether a cached snapshot can satisfy a project request."""
    is_eligible: bool
    reason: str
    dataset_hash_matched: bool
    schema_version_matched: bool
    expected_dataset_hash: str
    snapshot_dataset_hash: str
    expected_schema_version: str
    snapshot_schema_version: str


def check_snapshot_eligibility(
    snapshot: AnalysisSnapshot | dict[str, Any],
    expected_dataset_hash: str,
    expected_schema_version: str = "1.0.0"
) -> CacheEligibilityResult:
    """Evaluate whether an analysis snapshot is eligible to serve a given dataset.
    
    NON-NEGOTIABLE SAFETY RULES:
    1. The snapshot's dataset_hash must EXACTLY match the expected_dataset_hash.
       Never reuse cached analysis for modified or unrelated source material.
    2. The snapshot's schema_version must EXACTLY match expected_schema_version.
    """
    if isinstance(snapshot, AnalysisSnapshot):
        snap_hash = snapshot.dataset_hash
        snap_version = snapshot.schema_version
    else:
        snap_hash = snapshot.get("dataset_hash", "")
        snap_version = snapshot.get("schema_version", "")

    hash_match = bool(snap_hash and snap_hash == expected_dataset_hash)
    version_match = bool(snap_version and snap_version == expected_schema_version)

    if hash_match and version_match:
        reason = "Snapshot matches exact dataset hash and analysis schema version."
        is_eligible = True
    elif not hash_match and not version_match:
        reason = "Mismatch in both dataset hash and analysis schema version."
        is_eligible = False
    elif not hash_match:
        reason = "Dataset content mismatch: snapshot does not match the active source corpus."
        is_eligible = False
    else:
        reason = "Schema version mismatch: snapshot was generated with an incompatible schema."
        is_eligible = False

    return CacheEligibilityResult(
        is_eligible=is_eligible,
        reason=reason,
        dataset_hash_matched=hash_match,
        schema_version_matched=version_match,
        expected_dataset_hash=expected_dataset_hash,
        snapshot_dataset_hash=snap_hash,
        expected_schema_version=expected_schema_version,
        snapshot_schema_version=snap_version,
    )


def is_snapshot_eligible(
    snapshot: AnalysisSnapshot | dict[str, Any],
    expected_dataset_hash: str,
    expected_schema_version: str = "1.0.0"
) -> bool:
    """Convenience boolean check for cache snapshot eligibility."""
    return check_snapshot_eligibility(
        snapshot=snapshot,
        expected_dataset_hash=expected_dataset_hash,
        expected_schema_version=expected_schema_version
    ).is_eligible
