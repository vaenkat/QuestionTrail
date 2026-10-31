# QuestionTrail: Requirements and Acceptance Criteria

## Functional MVP

| ID | Measurable requirement |
|---|---|
| FLOW-01 | User can create a project from a free-text objective. |
| FLOW-02 | System proposes generic assessment categories with descriptions of relevant evidence. |
| FLOW-03 | User can add, rename, remove, enable/disable, or accept categories before analysis. |
| FLOW-04 | Approved objective/categories persist with the project/export. |
| SRC-01 | Curated source manifest includes original URL, authority/type, retrieved time, publication date/cycle when known, extraction state, and content. |
| SRC-02 | User can ingest a public URL and receives loading/success/actionable error state. |
| SRC-03 | User can upload a PDF and receives loading/success/actionable error state. |
| SRC-04 | Every important claim/finding exposes source ID, exact snippet, and page/section/URL location. |
| ANL-01 | Cross-source summary is organized by approved categories and cited. |
| ANL-02 | Each category is deterministically assessed as covered, partially covered, conflicting, unsupported, or requires verification. |
| ANL-03 | Potential conflicts show evidence on both sides and are not asserted as fact without contextual support. |
| ANL-04 | Dated evidence can be warned as old relative to the research context; undated evidence is labeled accordingly. |
| ANL-05 | No evidence found is distinguishable from explicitly negative evidence. |
| ANL-06 | Gaps and unanswered questions are calculated relative to the approved framework. |
| ACT-01 | Q&A responds only from project evidence or states that support is insufficient. |
| ACT-02 | Verification checklist includes deterministic priority, rationale, and official-source recommendation. |
| ACT-03 | Final report separates evidence, potential AI signals, and uncertainty. |
| REL-01 | One LLM interface supports NVIDIA, optional Gemini, and mock implementations. |
| REL-02 | Timeouts, quota/rate limits, unavailable models, and invalid structured output fail safely and observably. |
| REL-03 | Cache fallback requires exact dataset content hash plus analysis schema version and is visibly labeled. |
| REL-04 | Hashes, date logic, coverage, prioritization, and schema validation are deterministic and tested. |
| REL-05 | The application works locally and supports a single-service Cloud Run deployment with secrets server-side. |

## Demo acceptance test

A judge can complete the curated Reliance scenario in under five minutes: approve categories; inspect 4–6 sources; run/load analysis; open evidence behind claims, date warnings, conflicts, gaps, and checklist items; ask about renewal conditions and receive cited uncertainty if unsupported; export/view a final report. The same journey must work in explicitly labeled precomputed mode with live providers disabled.

## Stretch only after MVP passes

- A second small, non-scholarship corpus.
- Search-result selection before URL ingest.
- Cross-session project persistence/export-import beyond bundled data.
- Entity/relationship graph visualization.

## Test requirements

Unit-test deterministic utilities, source/evidence schema integrity, cache mismatch rejection, grounded-answer guard, provider failure paths, and prioritization. Integration-test curated analysis provenance, inaccessible URLs, corrupt PDFs, outdated documents, unsupported questions, quota exhaustion, and false-positive conflict handling. Use mock adapters by default; live calls are opt-in.
