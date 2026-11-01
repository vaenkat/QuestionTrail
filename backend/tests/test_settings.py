"""Tests for project-root .env resolution and credential privacy."""

import os
from pathlib import Path
import pytest
from pydantic import SecretStr

from questiontrail.settings import (
    Settings,
    _resolve_env_files,
    print_provider_status,
)
from questiontrail.llm.contracts import ProviderErrorKind, GenerationRequest
from questiontrail.llm.router import build_router_from_settings, AllProvidersExhausted
from questiontrail.services.analysis_orchestrator import (
    AnalysisOrchestrator,
    AnalysisUnavailableError,
)
from questiontrail.data.scholarship_corpus import (
    get_curated_sources,
    get_curated_categories,
    DEMO_OBJECTIVE,
)
from questiontrail.domain.models import Source, AssessmentCategory


def test_resolve_env_files_finds_project_root():
    """Verify that _resolve_env_files locates the root .env file."""
    files = _resolve_env_files()
    assert len(files) >= 1
    root_env = files[0]
    # Root .env must be located 4 levels up from questiontrail.settings
    settings_file = Path(__file__).resolve().parent.parent / "src" / "questiontrail" / "settings.py"
    expected_root_env = settings_file.parents[3] / ".env"
    assert root_env.resolve() == expected_root_env.resolve()


def test_clean_empty_keys_validator():
    """Verify that empty or whitespace-only keys in .env parse to None."""
    s = Settings(
        nvidia_api_key="",
        gemini_api_key="   ",
    )
    assert s.nvidia_api_key is None
    assert s.gemini_api_key is None
    assert s.has_nvidia_configured is False
    assert s.has_gemini_configured is False


def test_print_provider_status_never_exposes_secrets(capsys):
    """Verify print_provider_status prints only booleans and mode, never credential values."""
    secret_key = "nvapi-SUPER-SECRET-PLAINTEXT-KEY-12345"
    s = Settings(
        llm_provider="nvidia",
        nvidia_api_key=secret_key,
        gemini_api_key=None,
    )
    print_provider_status(s)
    captured = capsys.readouterr().out

    assert "Selected provider mode: nvidia" in captured
    assert "NVIDIA configured: True" in captured
    assert "Gemini configured: False" in captured
    # Critical: Secret key value MUST NOT appear in the output
    assert secret_key not in captured
    assert "SUPER-SECRET" not in captured


def test_curated_dataset_permits_precomputed_fallback_in_live_mode():
    """Rule 3: Curated dataset permits precomputed fallback even when in live mode with failed/unconfigured providers."""
    # Live mode with no credentials
    orchestrator = AnalysisOrchestrator(
        generation_service=None,
        provider_mode="auto",
    )
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


def test_arbitrary_source_raises_analysis_unavailable_in_live_mode():
    """Rule 4: Arbitrary uploaded sources without cached results raise AnalysisUnavailableError in live mode when providers fail."""
    orchestrator = AnalysisOrchestrator(
        generation_service=None,
        provider_mode="auto",
    )
    custom_sources = [
        Source(
            id="src-custom-1",
            title="Custom Source",
            raw_content="Custom text without any cached precomputed results.",
        )
    ]
    custom_cats = [
        AssessmentCategory(
            id="cat-1",
            name="Test",
            description="Test category",
            evaluation_question="Is this verified?",
            enabled=True,
        )
    ]

    with pytest.raises(AnalysisUnavailableError) as excinfo:
        orchestrator.analyze_project(
            project_id="proj-custom",
            objective="Evaluate custom source",
            sources=custom_sources,
            categories=custom_cats,
        )
    assert "Live AI analysis unavailable" in str(excinfo.value)
