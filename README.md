# QuestionTrail

Research evidence management and verification tool. Tracks claims, sources, and findings with full provenance.

---

## Prerequisites

- **Node.js** 20+ and npm
- **Python 3.13** and [uv](https://docs.astral.sh/uv/)

---

## Setup

### Backend

```bash
cd backend
uv sync
```

### Frontend

```bash
cd frontend
npm install
```

### Environment

Copy the example file and fill in real values only when using live providers:

```bash
cp .env.example .env
```

> **Default behaviour**: The backend runs in `mock` mode, which uses a deterministic local adapter.
> No API keys are required to run or test the project in this mode.

---

## Running locally

### Backend dev server

```bash
cd backend
uv run uvicorn questiontrail.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/health
```

### Frontend dev server

```bash
cd frontend
npm run dev
```

---

## Testing

### Backend

```bash
cd backend
uv run pytest -q
```

All tests run against the deterministic `MockAdapter` by default. No network calls are made. No API keys are needed.

### Frontend

```bash
cd frontend
npm run test -- --run
```

### Frontend build verification

```bash
cd frontend
npm run build
```

---

## LLM Provider configuration

The backend supports three provider modes, controlled by the `PROVIDER_MODE` environment variable in `.env`:

| Mode | Behaviour |
|------|-----------|
| `mock` (default) | Deterministic local adapter; no API key required |
| `nvidia` | NVIDIA NIM (OpenAI-compatible endpoint); requires `NVIDIA_API_KEY` |
| `gemini` | Google Gemini SDK; requires `GEMINI_API_KEY` |
| `auto` | Uses all configured live providers with mock fallback |

### Live smoke tests (opt-in only)

Live provider connectivity is **not tested by default**. To run a live smoke test, set credentials in `.env` and pass the `--live` marker explicitly (not yet implemented; tracked in Phase 2 plan). The automated CI suite never uses live credentials.

---

## Environment variables

See [`.env.example`](.env.example) for the full list. Never commit a `.env` file with real credentials.

---

## Project status

See [`docs/CURRENT_STATUS.md`](docs/CURRENT_STATUS.md) for the current implementation state and next steps.
