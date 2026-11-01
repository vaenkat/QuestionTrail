# QuestionTrail

> **Evidence-first AI research assistant and verification engine.**
> Ground every claim in verifiable source text, detect cross-source contradictions, identify knowledge gaps, and verify research with strict provenance.

[![Backend Tests](https://img.shields.io/badge/backend%20tests-101%20passed-teal)](backend/tests/)
[![Frontend Build](https://img.shields.io/badge/frontend-Vite%20%2B%20React%2019-blue)](frontend/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)

---

## 🎯 The Problem

Large Language Models (LLMs) summarize research persuasively, but they regularly:
1. **Hallucinate citations**: Fabricate plausible-sounding quotes or attribute assertions to sources that never made them.
2. **Overlook temporal drift**: Treat outdated information (e.g., past application deadlines or superseded criteria) as current fact.
3. **Gloss over contradictions**: Merge conflicting details from official vs. unofficial third-party portals without highlighting the discrepancy.
4. **Obscure provenance**: Present syntheses without exact location pointers (page number, section, exact quote) back to the original documents.

## 💡 The Solution: QuestionTrail

**QuestionTrail** reverses this dynamic by placing **uncompromising provenance at the center** of AI research:
- **Verbatim Evidence Enforcement**: Every extracted claim must cite an exact verbatim snippet present in the raw source bytes. If an LLM returns a synthesized quote, QuestionTrail verifies and anchors it against the genuine source content.
- **Cross-Source Contradiction Detection**: Discrepancies (such as conflicting deadlines, amounts, or eligibility requirements) are surfaced as dedicated findings with contrasting evidence links.
- **Coverage & Gap Analysis**: Evaluates your defined research categories against the source corpus to highlight unaddressed questions.
- **Safe Multi-Source Ingestion**: Ingest live web URLs (with strict SSRF guards), PDF files (with page-level tracking), or direct text alongside curated research benchmarks.
- **Prioritized Verification Checklist**: Generates an actionable, priority-ranked checklist of items that must be verified against primary official sources before making high-stakes decisions.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                          React 19 Frontend                             │
│  - Objective & Category Editor      - Contradiction & Gap Badges       │
│  - Multi-source Ingestion Tabs      - Slide-out Evidence Drawer        │
│  - Category Coverage Matrix         - Interactive Checklist & Export   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST
┌───────────────────────────────────▼────────────────────────────────────┐
│                         FastAPI Backend                                │
│                                                                        │
│  ┌────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │   Ingestion Service    │  │        Analysis Orchestrator         │  │
│  │  - SSRF-safe URL fetch │  │  - Category Coverage Evaluation      │  │
│  │  - PyMuPDF / pypdf     │  │  - Cross-Source Conflict Detection   │  │
│  │  - SHA-256 Hashing     │  │  - Date Freshness Classification     │  │
│  └────────────────────────┘  │  - Verification Action Scoring       │  │
│                              └──────────────────────────────────────┘  │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              Provider-Agnostic LLM Routing Engine                │  │
│  │   [NVIDIA NIM]  ───fallback───>  [Google Gemini]  ───fallback───>   │  │
│  │                          [Deterministic Mock]                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │               Deterministic Cache & Safety Layer                 │  │
│  │  - Canonical JSON serialization   - Schema version validation    │  │
│  │  - SHA-256 dataset fingerprint    - Verbatim quote verification  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 1. Multi-Source Ingestion
- **Curated Demo Corpus**: Reliance Foundation Undergraduate Scholarship 2026–27 dataset (includes official press release, application portal, 2024–25 archive FAQ with stale dates, and third-party education portals).
- **Runtime URL Ingestion**: Ingest any public web article or announcement. Protected by a **custom SSRF defense layer** that resolves DNS hostnames and rejects loopback, RFC 1918 private subnets, link-local, and reserved IP ranges.
- **PDF Document Ingestion**: Upload research PDFs (up to 10MB) with page-level text extraction and provenance.
- **Direct Text Input**: Paste raw excerpts, memos, or interview transcripts.

### 2. Provenance-Safe Analysis Engine
- **Verbatim Snippet Verification**: Validates that all claim citations exist verbatim inside `source.raw_content`.
- **Temporal Freshness Classification**: Classifies sources into `current`, `stale`, `archive`, or `future_dated` relative to an explicit reference date (`as_of`).
- **Deterministic Dataset Hashing**: Computes SHA-256 fingerprint over sorted, canonicalized source hashes and research objective. Prevents cache poisoning across modified corpora.

### 3. Provider-Independent LLM Routing
- **NVIDIA NIM**: Primary high-performance OpenAI-compatible inference (`meta/llama-3.1-70b-instruct`).
- **Google Gemini**: Secondary native SDK adapter (`gemini-2.5-flash`).
- **Deterministic Mock Provider**: Built-in offline adapter allowing the complete application and test suite to run with zero API keys or external network dependencies.

### 4. Interactive Research Dashboard
- **KPI Metrics**: Total claims, confirmed findings, potential findings, and verification actions.
- **Coverage Matrix**: Breakdown of status (`sufficient`, `partial`, `gap`) and evaluation questions per category.
- **Evidence Drawer**: Slide-out panel displaying exact snippet, source title, authority level, publication date, retrieval timestamp, and external URL.
- **Interactive Checklist**: High/medium/low priority actions with interactive completion tracking.
- **Report Export**: Instant export to Markdown format containing the executive synthesis, findings, and verification checklist.

---

## 🚀 Quickstart

### Prerequisites
- **Node.js 20+** and `npm`
- **Python 3.13** and [`uv`](https://docs.astral.sh/uv/)

### 1. Clone & Setup Backend

```bash
git clone https://github.com/Vaenkat/QuestionTrail.git
cd QuestionTrail/backend
uv sync
```

### 2. Setup Frontend

```bash
cd ../frontend
npm install
```

### 3. Environment Configuration

```bash
cd ..
cp .env.example .env
```

> **Zero-Configuration Offline Mode**: By default, `PROVIDER_MODE=mock`. The backend runs completely offline with deterministic mock responses. **No API keys are required to run, develop, or test QuestionTrail.**

To enable live LLM synthesis, edit `.env`:
```env
PROVIDER_MODE=auto            # or nvidia / gemini
NVIDIA_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

---

## 💻 Running Locally

### Start Backend API Server
```bash
cd backend
uv run uvicorn questiontrail.main:app --reload --port 8000
```
- API Health Check: `http://localhost:8000/api/health`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

### Start Frontend Dev Server
```bash
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Verification & Testing

QuestionTrail has a comprehensive automated test suite covering domain models, SSRF protection, ingestion, LLM failover, and API routes.

### Run Backend Tests (101 Tests)
```bash
cd backend
uv run pytest -q
```
Output:
```
101 passed, 1 warning in 0.90s
```

### Run Frontend Unit Tests
```bash
cd frontend
npm run test -- --run
```

### Run Frontend Production Build
```bash
cd frontend
npm run build
```

---

## 🔒 Security & Provenance Non-Negotiables

1. **SSRF Guardrail**: Ingestion URLs resolve DNS to canonical IPs prior to HTTP requests; loopback (`127.0.0.1`), private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), multicast, and cloud metadata endpoints (`169.254.169.254`) are blocked before transport initialization.
2. **Server-Side Credentials**: API keys for NVIDIA NIM and Gemini are strictly confined to the backend environment. No client-side leaks.
3. **Anti-Hallucination Integrity**: Claims require valid `EvidenceRef` with verbatim snippet, source ID, and location value. If the citation is unverified, it is automatically reconciled against source text.
4. **Cache Invalidation**: Adding any source or modifying categories immediately invalidates precomputed analysis caches.

---

## 📄 License

MIT License. Designed and developed for the **SHINCHAN ONLINE HACKATHON 2026**.
