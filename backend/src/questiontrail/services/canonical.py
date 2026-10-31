"""Deterministic canonical serialization and hashing services."""

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Any
from pydantic import BaseModel

from questiontrail.domain.models import AssessmentCategory, Source


def _normalize_for_canonical_json(val: Any) -> Any:
    """Recursively normalize data structures for deterministic JSON serialization."""
    if isinstance(val, BaseModel):
        return _normalize_for_canonical_json(val.model_dump())
    elif isinstance(val, dict):
        # Sort keys deterministically; recursively normalize values
        return {k: _normalize_for_canonical_json(v) for k, v in sorted(val.items())}
    elif isinstance(val, (list, tuple)):
        # Preserve array sequence order (do not sort arrays indiscriminately)
        return [_normalize_for_canonical_json(item) for item in val]
    elif isinstance(val, datetime):
        # Normalize datetimes to UTC ISO 8601 string
        if val.tzinfo is None:
            val = val.replace(tzinfo=timezone.utc)
        else:
            val = val.astimezone(timezone.utc)
        return val.isoformat()
    elif isinstance(val, date):
        return val.isoformat()
    elif isinstance(val, (str, int, float, bool)) or val is None:
        return val
    else:
        # Fallback to string representation for other scalar types
        return str(val)


def canonical_json(data: Any) -> str:
    """Produce deterministic canonical JSON representation.
    
    Rules:
    1. Dictionary keys are sorted recursively.
    2. Array order is preserved.
    3. Datetimes are formatted in UTC ISO 8601.
    4. Compact formatting with no whitespace: separators=(',', ':').
    """
    normalized = _normalize_for_canonical_json(data)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(data: str | bytes) -> str:
    """Compute SHA-256 hex digest of string or bytes."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def compute_content_hash(text: str) -> str:
    """Compute canonical hash of source content text."""
    # Normalize carriage returns
    normalized_text = text.replace("\r\n", "\n").replace("\r", "\n")
    return sha256_hex(normalized_text)


def extract_source_canonical_dict(source: Source | dict[str, Any]) -> dict[str, Any]:
    """Extract canonical analytical input fields from a source, excluding volatile metadata.
    
    Excludes `retrieved_at` or runtime fetch timings which do not alter analytical content.
    Includes id, title, url, type, authority, publication_date, cycle_or_version, and content_hash.
    """
    if isinstance(source, Source):
        s_dict = source.model_dump()
    else:
        s_dict = dict(source)

    # Compute content hash if raw content exists and hash is missing
    content_hash = s_dict.get("content_hash")
    if not content_hash and s_dict.get("raw_content"):
        content_hash = compute_content_hash(s_dict["raw_content"])

    return {
        "id": s_dict.get("id"),
        "title": s_dict.get("title"),
        "url": s_dict.get("url"),
        "type": str(s_dict.get("type", "")),
        "authority": str(s_dict.get("authority", "")),
        "publication_date": s_dict.get("publication_date"),
        "cycle_or_version": s_dict.get("cycle_or_version"),
        "content_hash": content_hash,
    }


def compute_dataset_hash(
    sources: list[Source | dict[str, Any]],
    objective: str | None = None,
    categories: list[AssessmentCategory | dict[str, Any]] | None = None
) -> str:
    """Compute deterministic SHA-256 hash representing complete analytical inputs.
    
    Components:
    1. Sources: sorted by `source.id` (set semantics for source corpus), containing only
       analytical provenance fields (excluding volatile retrieval timestamps).
    2. Objective: normalized stripped string.
    3. Categories: sorted by `category.id`, containing evaluation definition fields.
    """
    canonical_sources = [extract_source_canonical_dict(s) for s in sources]
    canonical_sources.sort(key=lambda s: str(s.get("id", "")))

    input_payload: dict[str, Any] = {
        "sources": canonical_sources,
    }

    if objective is not None:
        input_payload["objective"] = objective.strip()

    if categories is not None:
        canon_categories = []
        for cat in categories:
            if isinstance(cat, AssessmentCategory):
                c_dict = cat.model_dump()
            else:
                c_dict = dict(cat)
            canon_categories.append({
                "id": c_dict.get("id"),
                "name": c_dict.get("name"),
                "description": c_dict.get("description"),
                "evaluation_question": c_dict.get("evaluation_question"),
                "enabled": bool(c_dict.get("enabled", True)),
            })
        canon_categories.sort(key=lambda c: str(c.get("id", "")))
        input_payload["categories"] = canon_categories

    canonical_representation = canonical_json(input_payload)
    return sha256_hex(canonical_representation)
