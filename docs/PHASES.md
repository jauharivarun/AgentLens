# AgentLens — phase tracker

Status against [Implementation Plan](../docs%20for%20implementation/AgentLens_Final_All_Documents.md) (document 06).

Legend:

- **Done** — code is in the repo
- **Partial** — code exists but needs your keys, a live run, or a small follow-up
- **Not started** — not in this MVP yet

OpenAI is the live LLM provider. Groq stays a disabled adapter stub.

---

## PHASE 0 — Project setup

| Step | Status | Notes |
|---|---|---|
| 0.1 Repository layout | Done | `frontend/`, `backend/`, `sample_workspace/`, `docs/` |
| 0.2 React + Vite + TypeScript + Tailwind + Recharts | Done | Agent and Observability pages, shared layout |
| 0.3 FastAPI health + models | Done | `GET /api/health`, `GET /api/models` |

## PHASE 1 — Data and configuration

| Step | Status | Notes |
|---|---|---|
| 1.1 Environment files | Done | Keys live in `backend/.env` (root `.env` is not required) |
| 1.2 Model catalog | Done | Config-driven: `gpt-4o-mini`, `gpt-4o`. Frontend reads `/api/models` |

## PHASE 2 — LLM Gateway

| Step | Status | Notes |
|---|---|---|
| 2.1 Normalized `LLMResult` | Done | `backend/app/gateway/types.py` |
| 2.2 Provider adapter | Done | OpenAI live. Groq stub only |
| 2.3 Usage extraction tests | Done | Missing fields stay `null`, never `0` |

## PHASE 3 — Telemetry engine

| Step | Status | Notes |
|---|---|---|
| 3.1 `TelemetryRecorder` | Done | Start/complete/fail + LLM/tool/RAG/edit events |
| 3.2 LLM instrumentation in the gateway | Done | Usage, timing, estimated cost |
| 3.3 Tool instrumentation | Done | Start/end/status/latency/retry |

## PHASE 4 — Agent runtime

| Step | Status | Notes |
|---|---|---|
| 4.1 Tool registry | Done | `list_files`, `read_file`, `search_files`, `write_file`, `run_command`, `rag_search` |
| 4.2 Agent loop | Done | Max 12 iterations |
| 4.3 Safety | Done | Workspace boundary, command allowlist, timeouts, output limits |

## PHASE 5 — Sample workspace

| Step | Status | Notes |
|---|---|---|
| Demo repo + knowledge docs | Done | `sample_workspace/` with CSV, Python app, tests, markdown knowledge |

## PHASE 6 — RAG

| Step | Status | Notes |
|---|---|---|
| 6.1 Chroma Cloud client | Done | Env vars set in `backend/.env`. First backend start will ingest into Chroma |
| 6.2 Ingestion (MD/TXT) | Done | Auto-ingest on startup; local fallback without Chroma |
| 6.3 `rag_search` | Done | Agent tool + retrieval |
| 6.4 RAG telemetry | Done | Query hash, latency, chunk counts |
| PDF ingestion | Not started | Spec says add only after core MD/TXT works |

## PHASE 7 — Database

| Step | Status | Notes |
|---|---|---|
| 7.1 Schema | Done | You ran `schema.sql` in the Supabase SQL Editor; tables show in Table Editor |
| 7.2 Persistence | Done | Supabase keys are in `backend/.env`. Confirm rows appear after the first live run |
| 7.3 Failure tolerance | Done | Telemetry failures do not crash the agent |

## PHASE 8 — Agent page

| Step | Status | Notes |
|---|---|---|
| Model dropdown, task type, RAG, comparison group, Run | Done | Model is not injected into the prompt |
| Live trace + fingerprint + final answer | Done | Polling (not SSE) |

## PHASE 9 — Observability page

| Step | Status | Notes |
|---|---|---|
| 9.1 Summary cards | Done | Executions, LLM calls, tokens, cost, duration |
| 9.2 Token analytics | Partial | Tokens-by-model bar chart. No time-series trend yet |
| 9.3 Model analytics table | Done | Labeled “Based on your observed runs.” |
| 9.4 Tool analytics | Done | Counts, success, retries, latency |
| 9.5 Execution history + detail | Done | Click a row for trace, code impact, workflow, context |

## PHASE 10 — Comparison

| Step | Status | Notes |
|---|---|---|
| 10.1 Comparison group UI | Done | Create/select on the Agent page |
| 10.2 Associate executions | Done | Sent with `comparison_group_id` |
| 10.3 Side-by-side table | Done | Observed differences only; no winner badge |

## PHASE 11 — Innovation layer

| Step | Status | Notes |
|---|---|---|
| Execution fingerprint | Done | Compact card after a run |
| Model efficiency profile | Done | Observed-run table |
| Context efficiency | Done | Shown on execution detail when RAG/usage exists |
| Execution trace | Done | Expandable timeline |
| Automatic model routing | Not started | Explicitly out of V1 |

## PHASE 12 — Testing

| Step | Status | Notes |
|---|---|---|
| Unit tests (usage, cost, telemetry, tools, API) | Done | `cd backend && PYTHONPATH=. pytest` — 16 passed |
| Live agent tests (Q&A, file write, RAG, retry) | Not started | Needs `OPENAI_API_KEY` and a real run |

## PHASE 13 — Demo scenarios

| Step | Status | Notes |
|---|---|---|
| Example prompts in the Agent sidebar | Done | Four scenarios from the spec |
| Polished live walkthrough | Not started | Do this after adding your OpenAI key |

## PHASE 14 — Local testing checklist

| Check | Status |
|---|---|
| Frontend starts | Done (`npm run dev` / `npm run build`) |
| Backend health + models | Done |
| Agent run with tools | Not started (needs API key) |
| Observability updates after a run | Not started (needs a completed execution) |
| Comparison of two models | Not started |

## PHASE 15 — Deployment

| Step | Status | Notes |
|---|---|---|
| Vercel config | Partial | `vercel.json` exists. App is not deployed yet |
| Env vars on Vercel | Not started | Add keys in the Vercel dashboard when you deploy |

## PHASE 16 — Hardening

| Step | Status | Notes |
|---|---|---|
| No API keys in frontend | Done | Installation id only; catalog has no secrets |
| `.env` gitignored | Done | |
| No fake metrics | Done | `N/A` when unknown; cost N/A without pricing |
| Loading/error states | Partial | Present; polish after first live run |

## PHASE 17 — Assignment writeup

| Step | Status | Notes |
|---|---|---|
| Why/architecture/trade-offs document | Not started | Write after you have used the live demo |

---

## Your next steps (in order)

1. Start backend + frontend and run the four demo prompts — **Phases 12–14**
2. Confirm Observability updates and Supabase tables get rows
3. Deploy to Vercel — **Phase 15**
4. Write the assignment document — **Phase 17**

P1/P2 (not blocking): SSE streaming, live Groq, PDF ingest, export JSON/CSV, extra charts.
