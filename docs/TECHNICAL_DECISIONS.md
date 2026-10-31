# Technical Decisions

| Date | Decision | Rationale | Rejected / deferred |
|---|---|---|---|
| 2026-10-31 | Domain-neutral evidence model | Scholarship is a demo, while QuestionTrail must serve other research domains. | Scholarship-specific core fields and logic. |
| 2026-10-31 | Curated vertical slice first | A reliable judge journey is worth more than broad but incomplete ingestion. | Building live crawling/search first. |
| 2026-10-31 | Editable AI-proposed categories | Fast default flow while preserving user control and reproducibility. | Hardcoded topic templates and a complex rule builder. |
| 2026-10-31 | Deterministic logic for verifiable operations | Makes cache, dates, coverage, validation, and priority explainable and testable. | Letting LLM output determine all statuses. |
| 2026-10-31 | NVIDIA NIM primary, Gemini optional | Reduces paid-Gemini dependency; isolates vendors behind one interface. | Direct provider calls in business/UI code. |
| 2026-10-31 | Content-addressed precomputed fallback | Preserves a no-provider demo without returning stale/irrelevant analysis. | Generic fallback cache or hardcoded results. |
| 2026-10-31 | One FastAPI + static frontend Cloud Run service | Simplifies deploy and avoids CORS/configuration overhead. | Microservices, Kubernetes, split deployment by default. |
| 2026-10-31 | JSON/bundled persistence for MVP | Deadline and demo do not justify a database. | Database, queues, auth, and collaboration. |
| 2026-10-31 | shadcn/ui official primitives with custom evidence components | Gives Phase 1 accessible, consistent controls while preserving a distinctive research-intelligence workspace. | Multiple component libraries and a fully manual primitive set. |
| 2026-10-31 | Defer Recharts and React Flow | Charts and graphs must consume real analytical data; installing them in the foundation phase adds unused surface area. | Decorative or fabricated Phase 1 visualizations. |

## Change protocol

Add a dated row whenever a decision changes a core contract, dependency, provider, API surface, deployment model, or data store. Do not reverse a decision above without recording the evidence, migration impact, and reason.
