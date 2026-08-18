# Deploying AgentLens

The app is served from **one Vercel URL**. Vercel hosts the built frontend and rewrites
`/api/*` to a FastAPI backend running on **Render**.

## Why the backend is not on Vercel

AgentLens starts an agent run as a background `asyncio` task and the browser polls it for
progress (`backend/app/api/executions.py`). Serverless functions are frozen the moment they
return a response, so that background task never finishes — the UI would spin forever.

The read-only serverless filesystem is the second problem: it breaks file uploads,
the agent's `write_file` tool, and `run_tests`. Inspect → edit → run tests is the most
substantial thing this agent does, so it was worth keeping.

Running the backend on a persistent host preserves every capability. Proxying through
Vercel keeps a single public URL, and because the browser sees same-origin requests, the
custom `X-Installation-Id` header never triggers a CORS preflight.

## Deploy order

The backend must exist first, because Vercel's rewrite needs its URL.

### 1. Push to GitHub

Everything must be committed — `backend/app/telemetry/store.py` and
`frontend/src/components/FileViewer.tsx` are imported by other modules, so a deploy without
them fails at import.

### 2. Backend on Render

1. New → Blueprint, point it at this repo. It reads [`render.yaml`](render.yaml).
2. Render prompts for the secrets declared there: `OPENAI_API_KEY`, `GROQ_API_KEY`,
   `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `CHROMA_API_KEY`, `CHROMA_TENANT`,
   `CHROMA_DATABASE`. Only `OPENAI_API_KEY` is strictly required; without Supabase the
   telemetry falls back to in-memory, and without Chroma the RAG falls back to local search.
3. Set `CORS_ORIGINS` to your Vercel domain once you have it.
4. Confirm the service URL. Render appends a suffix if `agentlens-api` is taken —
   if yours differs, update it in **`vercel.json`** and
   **`.github/workflows/keepalive.yml`**.
5. Check it: `curl https://<service>.onrender.com/api/health`

### 3. Frontend on Vercel

1. Import the repo, **Root Directory = repository root**. Do not set it to `frontend/` —
   that would pick up `frontend/vercel.json`, which has no rewrite, and every API call
   would 404.
2. No environment variables are needed. The browser only ever talks to `/api/*` on its own
   origin; all keys live on Render.
3. Deploy, then verify the proxy: `curl https://<app>.vercel.app/api/health`

### 4. Keep it warm

Render's free tier sleeps after 15 minutes idle and takes about a minute to wake.
[`.github/workflows/keepalive.yml`](.github/workflows/keepalive.yml) pings `/api/health`
every 10 minutes. Enable Actions on the repo, or use a free external pinger such as
cron-job.org if you would rather not depend on the repository staying active.

## Known limits of the free tier

- **Uploads are not durable.** Render's free filesystem is ephemeral, so uploaded files are
  lost on redeploy, restart, or spin-down. Startup re-ingest prunes the matching Chroma
  chunks, so nothing goes stale — the uploads are simply gone. Built-in knowledge under
  `sample_workspace/knowledge/` ships with the repo and always survives.
  Making uploads durable means moving them to Supabase Storage.
- **One instance only.** The run registry in `backend/app/agent/control.py` lives in process
  memory, so a run must be polled from the process that started it. Do not scale to
  multiple instances or uvicorn workers.
- **750 instance-hours/month.** Keeping the service awake continuously uses about 730 of
  them, so this should be the only free service in the Render workspace.
- **512 MB RAM.** `chromadb` is pinned and imported lazily, only on the first RAG call. If
  the build or runtime hits limits, the fix is the thin `chromadb-client` package or calling
  the Chroma Cloud REST API directly — this codebase only ever uses `CloudClient`.

## Local development

Unchanged, and still the fastest way to iterate. See the README quick start. Vite proxies
`/api` to `127.0.0.1:8000`, which mirrors what the Vercel rewrite does in production.
