"""FastAPI API routes for research project lifecycle, category proposal, analysis, and reports."""

import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, Field

from questiontrail.domain.models import (
    ResearchProject,
    AssessmentCategory,
    Source,
    SourceType,
    SourceAuthority,
    ExtractionStatus,
    AnalysisResult,
    ANALYSIS_SCHEMA_VERSION,
    utc_now,
)
from questiontrail.settings import Settings, get_settings
from questiontrail.services.category_service import CategoryService
from questiontrail.services.analysis_orchestrator import AnalysisOrchestrator
from questiontrail.services.structured_generation import StructuredGenerationService
from questiontrail.services.url_ingestion import fetch_and_extract_url, IngestionError
from questiontrail.services.pdf_ingestion import extract_pdf_source
from questiontrail.services.canonical import compute_content_hash
from questiontrail.llm.router import build_router_from_settings
from questiontrail.data.scholarship_corpus import (
    DEMO_OBJECTIVE,
    get_curated_sources,
    get_curated_categories,
)

router = APIRouter(prefix="/api", tags=["projects"])


# --- In-memory session store ---

class ProjectStore:
    def __init__(self) -> None:
        self.projects: dict[str, ResearchProject] = {}
        self.sources: dict[str, list[Source]] = {}
        self.results: dict[str, AnalysisResult] = {}


_store = ProjectStore()


def get_project_store() -> ProjectStore:
    return _store


def get_orchestrator(settings: Settings = Depends(get_settings)) -> AnalysisOrchestrator:
    router_instance = build_router_from_settings(settings)
    gen_service = StructuredGenerationService(router_instance)
    return AnalysisOrchestrator(generation_service=gen_service)


def get_category_service(settings: Settings = Depends(get_settings)) -> CategoryService:
    router_instance = build_router_from_settings(settings)
    gen_service = StructuredGenerationService(router_instance)
    return CategoryService(generation_service=gen_service)


# --- Request / Response schemas ---

class ProposeCategoriesRequest(BaseModel):
    objective: str = Field(..., min_length=3, description="Free-text research objective")


class ProposeCategoriesResponse(BaseModel):
    objective: str
    categories: list[AssessmentCategory]


class CreateProjectRequest(BaseModel):
    objective: str = Field(..., min_length=3, description="Free-text research objective")
    categories: list[AssessmentCategory] = Field(default_factory=list)


class IngestUrlRequest(BaseModel):
    url: str = Field(..., min_length=4, description="Public HTTP/HTTPS URL")


class IngestTextRequest(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=10)
    url: str | None = None
    publication_date: str | None = None


class ProjectDetailResponse(BaseModel):
    project: ResearchProject
    sources: list[Source]
    has_analysis: bool


class AnalyzeProjectResponse(BaseModel):
    result: AnalysisResult
    mode: str = Field(..., description="'precomputed', 'mock', or 'live'")


class ReportResponse(BaseModel):
    project_id: str
    objective: str
    summary: str
    markdown_report: str
    total_claims: int
    total_findings: int
    total_actions: int


# --- Endpoints ---

@router.post("/categories/propose", response_model=ProposeCategoriesResponse)
def propose_categories(
    req: ProposeCategoriesRequest,
    category_service: CategoryService = Depends(get_category_service),
) -> ProposeCategoriesResponse:
    """Generate structured, editable assessment categories from an objective."""
    try:
        categories = category_service.propose_categories(req.objective)
        return ProposeCategoriesResponse(
            objective=req.objective,
            categories=categories,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/projects", response_model=ResearchProject)
def create_project(
    req: CreateProjectRequest,
    store: ProjectStore = Depends(get_project_store),
) -> ResearchProject:
    """Create a new research project with approved categories."""
    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    project = ResearchProject(
        id=project_id,
        objective=req.objective.strip(),
        categories=req.categories,
        source_ids=[],
        analysis_schema_version=ANALYSIS_SCHEMA_VERSION,
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    store.projects[project_id] = project
    store.sources[project_id] = []
    return project


@router.get("/projects/{project_id}", response_model=ProjectDetailResponse)
def get_project(
    project_id: str,
    store: ProjectStore = Depends(get_project_store),
) -> ProjectDetailResponse:
    """Retrieve project details, ingested sources, and analysis state."""
    project = store.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    sources = store.sources.get(project_id, [])
    has_analysis = project_id in store.results

    return ProjectDetailResponse(
        project=project,
        sources=sources,
        has_analysis=has_analysis,
    )


@router.post("/projects/{project_id}/load-demo", response_model=ProjectDetailResponse)
def load_curated_demo(
    project_id: str,
    store: ProjectStore = Depends(get_project_store),
) -> ProjectDetailResponse:
    """Load the reviewed curated scholarship sources and categories into the project."""
    project = store.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    curated_sources = get_curated_sources()
    curated_categories = get_curated_categories()

    # Update project
    project.objective = DEMO_OBJECTIVE
    project.categories = curated_categories
    project.source_ids = [s.id for s in curated_sources]
    project.updated_at = utc_now()

    store.projects[project_id] = project
    store.sources[project_id] = curated_sources

    return ProjectDetailResponse(
        project=project,
        sources=curated_sources,
        has_analysis=project_id in store.results,
    )


@router.post("/projects/{project_id}/sources/url", response_model=ProjectDetailResponse)
def ingest_url_source(
    project_id: str,
    req: IngestUrlRequest,
    store: ProjectStore = Depends(get_project_store),
) -> ProjectDetailResponse:
    """Safely ingest public URL content with SSRF protection into project."""
    project = store.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    try:
        source = fetch_and_extract_url(req.url)
    except IngestionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    current_sources = store.sources.setdefault(project_id, [])
    # Check if source with identical URL or content hash already ingested
    existing = next((s for s in current_sources if s.url == source.url or s.content_hash == source.content_hash), None)
    if not existing:
        current_sources.append(source)
        project.source_ids = [s.id for s in current_sources]
        project.updated_at = utc_now()
        # Invalidate existing analysis for this project since source corpus changed
        if project_id in store.results:
            del store.results[project_id]

    return ProjectDetailResponse(
        project=project,
        sources=current_sources,
        has_analysis=project_id in store.results,
    )


@router.post("/projects/{project_id}/sources/pdf", response_model=ProjectDetailResponse)
async def ingest_pdf_source(
    project_id: str,
    file: UploadFile = File(...),
    store: ProjectStore = Depends(get_project_store),
) -> ProjectDetailResponse:
    """Upload and extract text from PDF document into project."""
    project = store.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    filename = file.filename or "uploaded.pdf"
    content = await file.read()
    try:
        source, _ = extract_pdf_source(content, filename=filename)
    except IngestionError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    current_sources = store.sources.setdefault(project_id, [])
    existing = next((s for s in current_sources if s.content_hash == source.content_hash), None)
    if not existing:
        current_sources.append(source)
        project.source_ids = [s.id for s in current_sources]
        project.updated_at = utc_now()
        if project_id in store.results:
            del store.results[project_id]

    return ProjectDetailResponse(
        project=project,
        sources=current_sources,
        has_analysis=project_id in store.results,
    )


@router.post("/projects/{project_id}/sources/text", response_model=ProjectDetailResponse)
def ingest_text_source(
    project_id: str,
    req: IngestTextRequest,
    store: ProjectStore = Depends(get_project_store),
) -> ProjectDetailResponse:
    """Add custom text content into project."""
    project = store.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    body_text = req.content.strip()
    content_hash = compute_content_hash(body_text)
    source = Source(
        id=f"src-text-{content_hash[:8]}",
        title=req.title.strip(),
        url=req.url,
        type=SourceType.document,
        authority=SourceAuthority.third_party,
        publication_date=req.publication_date,
        retrieved_at=utc_now(),
        extraction_status=ExtractionStatus.success,
        content_hash=content_hash,
        raw_content=body_text,
    )

    current_sources = store.sources.setdefault(project_id, [])
    current_sources.append(source)
    project.source_ids = [s.id for s in current_sources]
    project.updated_at = utc_now()
    if project_id in store.results:
        del store.results[project_id]

    return ProjectDetailResponse(
        project=project,
        sources=current_sources,
        has_analysis=project_id in store.results,
    )


@router.post("/projects/{project_id}/analyze", response_model=AnalyzeProjectResponse)
def analyze_project(
    project_id: str,
    store: ProjectStore = Depends(get_project_store),
    orchestrator: AnalysisOrchestrator = Depends(get_orchestrator),
) -> AnalyzeProjectResponse:
    """Run analysis across all project sources and categories."""
    project = store.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    sources = store.sources.get(project_id, [])
    if not sources:
        raise HTTPException(
            status_code=400,
            detail="Cannot analyze project with zero sources. Load demo sources or ingest a source first.",
        )

    categories = [c for c in project.categories if c.enabled]
    if not categories:
        raise HTTPException(
            status_code=400,
            detail="Cannot analyze project with zero enabled evaluation categories.",
        )

    result, mode = orchestrator.analyze_project(
        project_id=project_id,
        objective=project.objective,
        sources=sources,
        categories=categories,
    )

    store.results[project_id] = result
    project.dataset_hash = result.dataset_hash
    project.updated_at = utc_now()

    return AnalyzeProjectResponse(
        result=result,
        mode=mode,
    )


@router.get("/projects/{project_id}/report", response_model=ReportResponse)
def get_project_report(
    project_id: str,
    store: ProjectStore = Depends(get_project_store),
) -> ReportResponse:
    """Assemble a structured Markdown verification report for the project."""
    project = store.projects.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    result = store.results.get(project_id)
    if not result:
        raise HTTPException(
            status_code=400,
            detail=f"No analysis results available for project '{project_id}'. Run analysis first.",
        )

    # Format Markdown Report
    lines = [
        f"# Research Verification Report: {project_id}",
        f"\n**Objective:** {project.objective}\n",
        f"**Dataset Hash:** `{result.dataset_hash}`\n",
        f"**Generated:** {result.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n",
        "## Executive Summary\n",
        result.summary or "Analysis complete.",
        "\n## Category Assessments\n",
    ]

    for assess in result.assessments:
        cat_match = next((c for c in project.categories if c.id == assess.category_id), None)
        cat_name = cat_match.name if cat_match else assess.category_id
        lines.append(f"### {cat_name} — Status: `{assess.status.value.upper()}`")
        if assess.rationale:
            lines.append(f"*{assess.rationale}*\n")
        if assess.supporting_claim_ids:
            lines.append(f"- **Supporting Claims:** {len(assess.supporting_claim_ids)}")
        if assess.contrary_claim_ids:
            lines.append(f"- **Conflicting Claims:** {len(assess.contrary_claim_ids)}")
        if assess.unanswered_questions:
            lines.append("- **Unanswered Questions:**")
            for q in assess.unanswered_questions:
                lines.append(f"  - {q}")
        lines.append("")

    lines.append("## Identified Findings & Epistemic Signals\n")
    for f in result.findings:
        lines.append(
            f"- **[{f.type.value.upper()}]** (`{f.label.value}` | Severity: `{f.severity.value}`): {f.rationale}"
        )
        for ref in f.evidence_refs:
            lines.append(f"  > Quote: \"{ref.exact_snippet}\" (Source: `{ref.source_id}`)")

    lines.append("\n## Prioritized Verification Checklist\n")
    for idx, act in enumerate(result.actions, 1):
        lines.append(
            f"{idx}. **[Priority: {act.priority_score:.2f}]** {act.action}\n"
            f"   - *Rationale:* {act.rationale}\n"
            f"   - *Recommended Source:* {act.recommended_source or 'Official Portal'}"
        )

    markdown_content = "\n".join(lines)

    return ReportResponse(
        project_id=project_id,
        objective=project.objective,
        summary=result.summary or "",
        markdown_report=markdown_content,
        total_claims=len(result.claims),
        total_findings=len(result.findings),
        total_actions=len(result.actions),
    )
