"""Deterministic date parsing and freshness evaluation services."""

from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class FreshnessStatus(str, Enum):
    """Categorical freshness status of source evidence."""
    fresh = "fresh"
    stale = "stale"
    future_dated = "future_dated"
    undated = "undated"
    invalid_date = "invalid_date"


class FreshnessEvaluation(BaseModel):
    """Deterministic result of evaluating source freshness."""
    status: FreshnessStatus
    age_days: int | None = None
    as_of: datetime
    parsed_date: datetime | None = None
    raw_date: str | None = None
    warning_message: str | None = None


def normalize_to_utc(dt: datetime) -> datetime:
    """Normalize datetime to timezone-aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_date_safe(val: str | datetime | date | None) -> tuple[datetime | None, bool]:
    """Safely parse diverse date representations into a timezone-aware UTC datetime.
    
    Returns:
        (datetime_in_utc, is_valid_boolean)
    """
    if val is None:
        return None, False

    if isinstance(val, datetime):
        return normalize_to_utc(val), True

    if isinstance(val, date):
        # Convert date to midnight UTC datetime
        dt = datetime(val.year, val.month, val.day, 0, 0, 0, tzinfo=timezone.utc)
        return dt, True

    if isinstance(val, str):
        cleaned = val.strip()
        if not cleaned:
            return None, False

        # Replace 'Z' with '+00:00' for standard fromisoformat parsing if needed
        iso_candidate = cleaned
        if iso_candidate.endswith("Z"):
            iso_candidate = iso_candidate[:-1] + "+00:00"

        try:
            parsed = datetime.fromisoformat(iso_candidate)
            return normalize_to_utc(parsed), True
        except (ValueError, TypeError):
            pass

        # Try standard YYYY-MM-DD pattern
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%Y", "%B %d, %Y", "%d %B %Y"):
            try:
                parsed = datetime.strptime(cleaned, fmt)
                return parsed.replace(tzinfo=timezone.utc), True
            except (ValueError, TypeError):
                continue

    return None, False


def classify_freshness(
    publication_date: str | datetime | date | None,
    as_of: datetime,
    max_age_days: int = 365,
    future_grace_hours: int = 24
) -> FreshnessEvaluation:
    """Classify the freshness of source material relative to an explicit reference date.
    
    CRITICAL ENGINE RULES:
    1. NEVER read the system clock implicitly. `as_of` must be passed explicitly to ensure
       deterministic, reproducible classification across executions.
    2. Publication date is distinct from retrieval time.
    3. Future-dated sources are flagged for review rather than automatically treated as fresh.
    4. Undated sources return an explicit 'undated' status; dates are never inferred.
    """
    as_of_utc = normalize_to_utc(as_of)
    raw_str = str(publication_date) if publication_date is not None else None

    # Undated check
    if publication_date is None or (isinstance(publication_date, str) and not publication_date.strip()):
        return FreshnessEvaluation(
            status=FreshnessStatus.undated,
            as_of=as_of_utc,
            raw_date=raw_str,
            warning_message="Source does not provide a verifiable publication date."
        )

    parsed_dt, is_valid = parse_date_safe(publication_date)

    # Invalid date check
    if not is_valid or parsed_dt is None:
        return FreshnessEvaluation(
            status=FreshnessStatus.invalid_date,
            as_of=as_of_utc,
            raw_date=raw_str,
            warning_message=f"Publication date '{raw_str}' is malformed and could not be verified."
        )

    # Future date check (with optional slight grace period for timezone variance)
    grace_cutoff = as_of_utc + timedelta(hours=future_grace_hours)
    if parsed_dt > grace_cutoff:
        future_days = (parsed_dt.date() - as_of_utc.date()).days
        return FreshnessEvaluation(
            status=FreshnessStatus.future_dated,
            age_days=-future_days,
            as_of=as_of_utc,
            parsed_date=parsed_dt,
            raw_date=raw_str,
            warning_message=f"Source publication date is in the future (+{future_days} days relative to research context); requires review."
        )

    # Calculate elapsed age in whole days
    age_days = (as_of_utc.date() - parsed_dt.date()).days

    # Fresh vs Stale check
    if age_days > max_age_days:
        return FreshnessEvaluation(
            status=FreshnessStatus.stale,
            age_days=age_days,
            as_of=as_of_utc,
            parsed_date=parsed_dt,
            raw_date=raw_str,
            warning_message=f"Source is {age_days} days old relative to research context (threshold: {max_age_days} days)."
        )

    return FreshnessEvaluation(
        status=FreshnessStatus.fresh,
        age_days=age_days,
        as_of=as_of_utc,
        parsed_date=parsed_dt,
        raw_date=raw_str,
        warning_message=None
    )
