# AgentLens

**Build with AI. See what it costs.**

AgentLens is a two-page developer tool: a tool-using agent with a model selector, and an Observability page that records tokens, tools, latency, estimated cost, and task outcomes.

Model selection is UI state. The task prompt is never rewritten to mention a model name.

## What this MVP includes

- React / Vite / TypeScript frontend
- FastAPI backend
- OpenAI and Groq as live LLM providers
- LLM Gateway that captures provider usage and estimates cost
- Workspace tools: list/read/search/write files and allowlisted Python commands
- RAG over `sample_workspace/knowledge` (Chroma Cloud when configured, local fallback otherwise)
- Telemetry persisted to Supabase when configured, otherwise in-memory
- Manual same-task comparison groups
- Execution fingerprints and an observability dashboard

Groq runs through the same adapter path and appears in the dropdown once `GROQ_API_KEY` is set.

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
| `GROQ_API_KEY` | Groq models in the dropdown | Server-side only |

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

## Deploy

The app is served from one Vercel URL: Vercel hosts the built frontend and rewrites `/api/*` to a
FastAPI backend on Render.

The backend does not run on Vercel because an agent run is a background task that the browser polls,
and serverless functions are frozen as soon as they return a response — the run would never finish.
The read-only serverless filesystem also breaks uploads, `write_file`, and `run_tests`.

See [`DEPLOY.md`](DEPLOY.md) for the full sequence and the free-tier limits.

## Trust labels

Metrics are labeled as:

- **Provider reported** — token usage from the OpenAI response
- **Runtime measured** — latency, tool status, file diffs
- **Calculated** — estimated cost from versioned pricing
- **Heuristic** — workflow signals such as repeat-file rework

Unknown values render as `N/A`. AgentLens does not rank models or invent prices.
