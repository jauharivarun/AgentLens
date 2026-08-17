# AgentLens

**Build with AI. See what it costs.**

AgentLens is a two-page developer tool: a tool-using agent with a model selector, and an Observability page that records tokens, tools, latency, estimated cost, and task outcomes.

Model selection is UI state. The task prompt is never rewritten to mention a model name.

## What this MVP includes

- React / Vite / TypeScript frontend
- FastAPI backend
- OpenAI as the live LLM provider (`gpt-4o-mini`, `gpt-4o`)
- LLM Gateway that captures provider usage and estimates cost
- Workspace tools: list/read/search/write files and allowlisted Python commands
- RAG over `sample_workspace/knowledge` (Chroma Cloud when configured, local fallback otherwise)
- Telemetry persisted to Supabase when configured, otherwise in-memory
- Manual same-task comparison groups
- Execution fingerprints and an observability dashboard

Groq is registered as a provider adapter stub and stays disabled until `GROQ_API_KEY` is set.

## Phase tracker

See [`docs/PHASES.md`](docs/PHASES.md) for the step-by-step implementation checklist (Phases 0–17): what is done, what is partial, and what still needs your API keys or a live run.

## Quick start

```bash
cp .env.example .env
# put OPENAI_API_KEY in .env

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd backend
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Environment

| Variable | Required for | Notes |
|---|---|---|
| `OPENAI_API_KEY` | Live agent runs | Server-side only |
| `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` | Persistent telemetry | Optional; in-memory fallback is used without it |
| `CHROMA_API_KEY` / `CHROMA_TENANT` / `CHROMA_DATABASE` | Hosted RAG | Optional; local keyword/embedding fallback is used without it |
| `GROQ_API_KEY` | Future Groq adapter | Unused in this MVP |

Never put provider keys in the frontend. The browser only receives public model catalog fields.

## Supabase

1. Create a free Supabase project.
2. Run [`backend/sql/schema.sql`](backend/sql/schema.sql) in the SQL editor.
3. Copy the project URL and service role key into `.env`.

## Demo prompts

1. Explain the architecture of the sample workspace and identify the main execution path.
2. Create a Python utility that reads sales.csv and produces a summary report.
3. From the knowledge base, summarize the sustainability reporting requirements and cite the source documents.
4. Create a comparison group, run the same coding prompt on `gpt-4o-mini` and `gpt-4o`, then compare in Observability.

## Tests

```bash
cd backend
PYTHONPATH=. pytest
```

Usage tests verify that missing provider fields stay `null` (never guessed as zero) and that unknown model prices stay `N/A`.

## Deploy on Vercel

This repo is set up as a Vite frontend plus a Python `/api` function.

1. Import the GitHub repo in Vercel.
2. Set environment variables (`OPENAI_API_KEY`, and optionally Supabase/Chroma).
3. Deploy.

Serverless timeouts can cut long agent loops. Local `uvicorn` is the most reliable way to demo multi-step tool use.

## Trust labels

Metrics are labeled as:

- **Provider reported** — token usage from the OpenAI response
- **Runtime measured** — latency, tool status, file diffs
- **Calculated** — estimated cost from versioned pricing
- **Heuristic** — workflow signals such as repeat-file rework

Unknown values render as `N/A`. AgentLens does not rank models or invent prices.
