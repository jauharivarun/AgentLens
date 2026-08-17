import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import { AgentTurn, type AgentTurnData } from "../components/AgentTurn";
import { formatProvider } from "../lib/format";
import type { HistoryRow, ModelOption } from "../types";

const EXAMPLES = [
  "Explain the architecture of the sample workspace and identify the main execution path.",
  "Create a Python utility that reads sales.csv and produces a summary report.",
  "From the knowledge base, summarize the sustainability reporting requirements and cite the source documents.",
];

function fromHistory(row: HistoryRow): AgentTurnData {
  return {
    executionId: row.execution_id,
    prompt: row.task_text || row.task_preview,
    status: row.status,
    events: [],
    finalOutput: row.final_output ?? null,
    startedAt: row.started_at,
    fingerprint: row,
  };
}

export function AgentPage() {
  const [models, setModels] = useState<ModelOption[]>([]);
  const [task, setTask] = useState("");
  const [modelId, setModelId] = useState("");
  const [ragEnabled, setRagEnabled] = useState(false);
  const [running, setRunning] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<AgentTurnData[]>([]);
  const [health, setHealth] = useState<{ openai_configured?: boolean; groq_configured?: boolean } | null>(null);
  const [uploads, setUploads] = useState<{ name: string; path: string; bytes: number }[]>([]);
  const [uploading, setUploading] = useState(false);
  const composerRef = useRef<HTMLTextAreaElement>(null);
  const threadEndRef = useRef<HTMLDivElement>(null);

  const selected = useMemo(() => models.find((item) => `${item.provider}:${item.model_id}` === modelId), [models, modelId]);

  useEffect(() => {
    api.models().then((data) => {
      setModels(data.models);
      if (data.models[0]) setModelId(`${data.models[0].provider}:${data.models[0].model_id}`);
    }).catch((err) => setError(err.message));
    api.health().then(setHealth).catch(() => undefined);
    api.uploads().then((data) => setUploads(data.files)).catch(() => undefined);
    api.history("").then(async (data) => {
      const loaded = data.executions.slice(0, 20).reverse().map(fromHistory);
      setTurns((current) => {
        if (!current.length) return loaded;
        const existing = new Set(current.map((turn) => turn.executionId));
        return [...loaded.filter((turn) => !existing.has(turn.executionId)), ...current];
      });
      const live = data.executions.find((row) => row.status === "running" || row.status === "queued");
      if (live) {
        setExecutionId((current) => current ?? live.execution_id);
        setRunning(true);
      }
      const withEvents = await Promise.all(
        loaded.map(async (turn) => {
          try {
            const detail = await api.events(turn.executionId);
            return {
              ...turn,
              status: detail.status || turn.status,
              events: detail.events,
              finalOutput: detail.final_output ?? turn.finalOutput,
              fingerprint: detail.fingerprint || turn.fingerprint,
            };
          } catch {
            return turn;
          }
        }),
      );
      setTurns((current) => {
        const byId = new Map(withEvents.map((turn) => [turn.executionId, turn]));
        return current.map((turn) => {
          const fresh = byId.get(turn.executionId);
          if (!fresh) return turn;
          return turn.events.length ? turn : fresh;
        });
      });
    }).catch(() => undefined);
  }, []);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, executionId]);

  useEffect(() => {
    if (!executionId) return;
    let cancelled = false;
    const poll = async () => {
      try {
        const data = await api.events(executionId);
        if (cancelled) return;
        setTurns((current) =>
          current.map((turn) =>
            turn.executionId === executionId
              ? {
                  ...turn,
                  status: data.status,
                  events: data.events,
                  finalOutput: data.final_output,
                  fingerprint: data.fingerprint,
                }
              : turn,
          ),
        );
        if (data.status === "running" || data.status === "queued") {
          window.setTimeout(poll, 900);
        } else {
          setRunning(false);
          setStopping(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Polling failed");
          setRunning(false);
          setStopping(false);
        }
      }
    };
    poll();
    return () => {
      cancelled = true;
    };
  }, [executionId]);

  async function onRun(event: FormEvent) {
    event.preventDefault();
    if (!selected || !task.trim()) return;
    const prompt = task.trim();
    setError(null);
    setRunning(true);
    try {
      const result = await api.startExecution({
        task: prompt,
        model: { provider: selected.provider, model_id: selected.model_id },
        task_type: ragEnabled ? "rag" : "general",
        comparison_group_id: null,
        rag_enabled: ragEnabled,
        workspace_id: "demo-workspace",
      });
      setTurns((current) => [
        ...current.filter((turn) => turn.executionId !== result.execution_id),
        {
          executionId: result.execution_id,
          prompt,
          status: "running",
          events: [],
          finalOutput: null,
          fingerprint: null,
          startedAt: new Date().toISOString(),
        },
      ]);
      setExecutionId(result.execution_id);
      setTask("");
    } catch (err) {
      setRunning(false);
      setError(err instanceof Error ? err.message : "Failed to start execution");
    }
  }

  async function onStop() {
    if (!executionId || stopping) return;
    setStopping(true);
    setError(null);
    try {
      await api.stopExecution(executionId);
    } catch {
      setTurns((current) =>
        current.map((turn) =>
          turn.executionId === executionId
            ? { ...turn, status: "cancelled", finalOutput: turn.finalOutput || "Stopped by user." }
            : turn,
        ),
      );
      setRunning(false);
      setStopping(false);
    }
  }

  function reusePrompt(prompt: string) {
    setTask(prompt);
    composerRef.current?.focus();
    composerRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  async function loadTrace(id: string) {
    try {
      const data = await api.events(id);
      setTurns((current) =>
        current.map((turn) =>
          turn.executionId === id
            ? { ...turn, events: data.events, finalOutput: data.final_output ?? turn.finalOutput, fingerprint: data.fingerprint }
            : turn,
        ),
      );
    } catch {
      setError("Could not load execution steps.");
    }
  }

  const recent = [...turns].reverse().slice(0, 8);

  return (
    <div className="grid min-h-[calc(100vh-61px)] grid-cols-1 lg:grid-cols-[minmax(0,260px)_minmax(0,1fr)]">
      <aside className="min-w-0 overflow-hidden border-b border-[var(--border)] bg-[var(--panel)] p-4 lg:border-b-0 lg:border-r">
        <div className="text-xs uppercase tracking-wide text-[var(--muted)]">Workspace</div>
        <div className="mt-2 text-sm">Demo repo</div>
        <div className="mono mt-1 truncate text-xs text-[var(--muted)]">sample_workspace</div>
        <ul className="mt-4 min-w-0 space-y-1 text-sm text-[var(--muted)]">
          <li>data/sales.csv</li>
          <li>src/report.py</li>
          <li>tests/test_report.py</li>
          <li>knowledge/*.md</li>
          {uploads.map((file) => (
            <li key={file.path} className="truncate" title={`uploads/${file.name}`}>
              uploads/{file.name}
            </li>
          ))}
        </ul>
        <div className="mt-6 text-xs uppercase tracking-wide text-[var(--muted)]">Example tasks</div>
        <div className="mt-2 space-y-2">
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              className="block w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] p-2 text-left text-xs text-[var(--muted)] hover:text-white"
              onClick={() => setTask(example)}
            >
              {example}
            </button>
          ))}
        </div>
        {recent.length ? (
          <>
            <div className="mt-6 text-xs uppercase tracking-wide text-[var(--muted)]">Recent runs</div>
            <div className="mt-2 space-y-2">
              {recent.map((turn) => (
                <button
                  key={turn.executionId}
                  type="button"
                  className="block w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] p-2 text-left text-xs text-[var(--muted)] hover:text-white"
                  onClick={() =>
                    document.getElementById(`turn-${turn.executionId}`)?.scrollIntoView({ behavior: "smooth", block: "start" })
                  }
                >
                  <div className="line-clamp-2">{turn.prompt}</div>
                  <div className="mt-1 text-[11px] text-[var(--muted)]">
                    {turn.fingerprint?.model || turn.status}
                  </div>
                </button>
              ))}
            </div>
          </>
        ) : null}
      </aside>

      <section className="flex min-h-0 min-w-0 flex-col">
        <div className="flex-1 space-y-6 overflow-auto p-5">
          {health && health.openai_configured === false && health.groq_configured === false ? (
            <div className="rounded-lg border border-[var(--warning)]/40 bg-[var(--warning)]/10 px-3 py-2 text-sm">
              Add OPENAI_API_KEY and/or GROQ_API_KEY to backend/.env, then restart the backend.
            </div>
          ) : null}
          {error ? (
            <div className="rounded-lg border border-[var(--error)]/40 bg-[var(--error)]/10 px-3 py-2 text-sm">{error}</div>
          ) : null}
          {!turns.length && !running ? (
            <p className="text-sm text-[var(--muted)]">Give the agent a task to start an execution. Previous prompts and answers stay on this page for comparison; they are not sent back to the model.</p>
          ) : (
            <div className="space-y-8">
              {turns.length ? (
                <p className="text-xs text-[var(--muted)]">
                  Run history on this page is for comparison only. Each run is independent.
                </p>
              ) : null}
              {turns.map((turn) => (
                <AgentTurn
                  key={turn.executionId}
                  turn={turn}
                  live={turn.executionId === executionId && running}
                  onReuse={reusePrompt}
                  onToggleTrace={loadTrace}
                />
              ))}
              <div ref={threadEndRef} />
            </div>
          )}
        </div>

        <form onSubmit={onRun} className="border-t border-[var(--border)] bg-[var(--panel)] p-4">
          <textarea
            ref={composerRef}
            value={task}
            onChange={(event) => setTask(event.target.value)}
            placeholder="Describe a task. Attach a file if you want the agent to read it. The selected model is not added to this prompt."
            className="h-24 w-full resize-none rounded-lg border border-[var(--border)] bg-[var(--bg)] p-3 text-sm outline-none focus:border-[var(--accent)]"
          />
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <label className="inline-flex items-center gap-2 text-xs text-[var(--muted)]">
              Attach file
              <span className="inline-flex cursor-pointer items-center rounded-md border border-white/40 bg-white px-3 py-1.5 text-xs font-medium text-black hover:bg-white/90">
                Choose file
                <input
                  type="file"
                  accept=".md,.txt,.csv,.json,.py"
                  className="sr-only"
                  disabled={uploading}
                  onChange={async (event) => {
                    const file = event.target.files?.[0];
                    event.target.value = "";
                    if (!file) return;
                    setUploading(true);
                    setError(null);
                    try {
                      await api.upload(file);
                      const listed = await api.uploads();
                      setUploads(listed.files);
                      setRagEnabled(true);
                    } catch (err) {
                      setError(err instanceof Error ? err.message : "Upload failed");
                    } finally {
                      setUploading(false);
                    }
                  }}
                />
              </span>
            </label>
            {uploading ? <span className="text-xs text-[var(--muted)]">Indexing…</span> : null}
            {uploads.length ? (
              <span
                className="min-w-0 flex-1 truncate text-xs text-[var(--muted)]"
                title={uploads.map((file) => file.name).join(", ")}
              >
                In knowledge: {uploads.map((file) => file.name).join(", ")}
              </span>
            ) : null}
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <label className="text-xs text-[var(--muted)]">
              Model
              <select
                value={modelId}
                onChange={(event) => setModelId(event.target.value)}
                className="ml-2 rounded-md border border-[var(--border)] bg-[var(--bg)] px-2 py-1 text-sm text-white"
              >
                {models.map((model) => (
                  <option key={`${model.provider}:${model.model_id}`} value={`${model.provider}:${model.model_id}`}>
                    {formatProvider(model.provider)} / {model.display_name}
                    {model.context_window ? ` · ${Math.round(model.context_window / 1000)}k` : ""}
                    {model.configured ? "" : " (not configured)"}
                  </option>
                ))}
              </select>
            </label>
            <span className="hidden h-5 w-px bg-[var(--border)] sm:block" aria-hidden="true" />
            <label className="flex items-center gap-2 text-xs text-[var(--muted)]" title="Search uploaded files and the knowledge folder">
              <input type="checkbox" checked={ragEnabled} onChange={(event) => setRagEnabled(event.target.checked)} />
              Search knowledge
            </label>
            {running ? (
              <button
                type="button"
                onClick={onStop}
                disabled={stopping}
                className="ml-auto rounded-md bg-[var(--error)] px-4 py-1.5 text-sm font-medium text-white disabled:opacity-40"
              >
                {stopping ? "Stopping…" : "Stop"}
              </button>
            ) : (
              <button
                type="submit"
                disabled={!task.trim()}
                className="ml-auto rounded-md bg-[var(--accent)] px-4 py-1.5 text-sm font-medium text-black disabled:opacity-40"
              >
                Run
              </button>
            )}
          </div>
        </form>
      </section>
    </div>
  );
}
