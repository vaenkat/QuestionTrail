# QuestionTrail: Technical Architecture

## Deployment and components

One Cloud Run container serves the built React/TypeScript/Vite/Tailwind frontend and a FastAPI backend at `/api`. Locally, Vite proxies `/api` to FastAPI. No database is required for MVP: curated assets, JSON manifests/snapshots, and lightweight browser/session state are sufficient.

| Layer | Responsibility |
|---|---|
| React UI | Objective/category review, source states, dashboard, evidence drawer, Q&A, report/checklist |
| FastAPI routes | Validation, project/source/analysis endpoints, static assets, health check |
| Research services | Category proposal, evidence chunking, orchestration, assessments, report assembly |
| Deterministic services | SHA-256 canonicalization, dates, cache eligibility, coverage, scoring, schema/provenance checks |
| Source adapters | Safe public URL extraction (Trafilatura then BeautifulSoup), PDF text/page extraction (PyMuPDF) |
| LLM service | Provider-neutral structured generation and bounded provider routing |
| Bundled data | Curated manifest, extracted source text, analysis snapshot, fixtures |

## Core data contracts

All contracts should be Pydantic models and JSON serializable. Keep field names generic.

| Model | Required fields |
|---|---|
| `ResearchProject` | id, objective, categories, source_ids, dataset_hash, analysis_schema_version |
| `AssessmentCategory` | id, name, description, evaluation_question, enabled |
| `Source` | id, title, URL, type, authority, publication_date, cycle_or_version, retrieved_at, extraction_status, content_hash |
| `EvidenceRef` | source_id, exact_snippet, location_type, location_value, offsets/page, metadata |
| `Claim` | id, normalized_statement, entities, dates, evidence_refs, extraction_status |
| `CategoryAssessment` | category_id, status, supporting_claim_ids, contrary_claim_ids, unanswered_questions |
| `Finding` | id, type, label (`potential`/`confirmed`), evidence_refs, severity, rationale |
| `VerificationAction` | id, priority_score, action, rationale, recommended_source, linked_ids |
| `AnalysisSnapshot` | dataset_hash, schema_version, provider, model, analysis payload, created_at |

## API contract plan

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Service and configured-provider status without secrets |
| `GET /api/demo/projects/{id}` | Curated project/manifest |
| `POST /api/categories/propose` | Structured category suggestions from objective |
| `POST /api/projects` | Create project with approved categories |
| `POST /api/projects/{id}/sources/url` | Safely ingest public URL |
| `POST /api/projects/{id}/sources/pdf` | Upload/extract PDF |
| `POST /api/projects/{id}/analyze` | Analyze current project sources and categories |
| `POST /api/projects/{id}/ask` | Grounded project question |
| `GET /api/projects/{id}/report` | Assemble evidence-aware research report |

Endpoint shapes are plans, not implemented contracts, until source files and tests exist.

## LLM abstraction

`LLMService.generate_structured(request, response_schema)` routes using `LLM_PROVIDER=auto|nvidia|gemini|mock` and `LLM_FALLBACK_ORDER=nvidia,gemini,cache`. NVIDIA NIM uses its OpenAI-compatible endpoint and reads `NVIDIA_API_KEY`/`NVIDIA_MODEL` only on the backend. Gemini reads optional `GEMINI_API_KEY`. The router records provider/model/mode/errors, validates schema responses, and uses bounded retries only for transient failures.

Cache is a last fallback only for an exact `(dataset_hash, analysis_schema_version)` match. It must show **Precomputed analysis** in the UI and must never satisfy an arbitrary user-source project.

## Deterministic boundary and safety

Application code owns hash generation, cache match, date comparison, coverage aggregation, priority scoring, evidence ID integrity, and response-schema validation. LLMs may propose categories, extract/normalize claims, identify candidate semantic conflicts, synthesize summaries, and suggest verification actions.

URL fetches allow HTTP(S) only, must block private/local network destinations, and apply content type, size, and timeout limits. API keys are never sent to the browser, source control, reports, or logs.

## Environment and commands

Expected variables (not yet implemented): `NVIDIA_API_KEY`, `NVIDIA_MODEL`, `GEMINI_API_KEY` (optional), `LLM_PROVIDER`, `LLM_FALLBACK_ORDER`. Add exact install/run/test commands only when the scaffold exists and they have been executed.
