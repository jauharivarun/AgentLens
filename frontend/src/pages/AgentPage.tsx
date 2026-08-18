import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import { AgentTurn, type AgentTurnData } from "../components/AgentTurn";
import { KnowledgeFilesPanel } from "../components/KnowledgeFilesPanel";
import { formatProvider } from "../lib/format";
import type { HistoryRow, ModelOption } from "../types";

const CHAT_STORAGE_KEY = "agentlens.chats";

type ChatSession = {
  id: string;
  title: string;
  named?: boolean;
  turns: AgentTurnData[];
};

type StoredTurn = { id: string; prompt?: string };

/** `executionIds` is the older shape, kept so existing chats survive the upgrade. */
type StoredChat = { id: string; title: string; named?: boolean; turns?: StoredTurn[]; executionIds?: string[] };

function storedTurns(chat: StoredChat): StoredTurn[] {
  if (Array.isArray(chat.turns)) return chat.turns.filter((turn) => turn && turn.id);
  return (chat.executionIds || []).map((id) => ({ id }));
}

function createChat(): ChatSession {
  return { id: crypto.randomUUID(), title: "New chat", turns: [] };
}

function displayTitle(chat: Pick<ChatSession, "title" | "named" | "turns">): string {
  if (chat.named && chat.title.trim()) return chat.title.trim();
  return titleFromTurns(chat.turns, chat.title);
}

function titleFromTurns(turns: AgentTurnData[], fallback = "New chat"): string {
  const prompt = turns[0]?.prompt?.trim();
  if (!prompt) return fallback;
  return prompt.length > 56 ? `${prompt.slice(0, 56)}…` : prompt;
}

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

function loadStoredChats(): { chats: StoredChat[]; activeChatId: string } | null {
  try {
    const raw = localStorage.getItem(CHAT_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { chats?: StoredChat[]; activeChatId?: string };
    if (!Array.isArray(parsed.chats) || !parsed.chats.length) return null;
    return { chats: parsed.chats, activeChatId: parsed.activeChatId || parsed.chats[0].id };
  } catch {
    return null;
  }
}

export function AgentPage() {
  const bootstrap = useMemo(() => createChat(), []);
  const [models, setModels] = useState<ModelOption[]>([]);
  const [task, setTask] = useState("");
  const [modelId, setModelId] = useState("");
  const [ragEnabled, setRagEnabled] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chats, setChats] = useState<ChatSession[]>([bootstrap]);
  const [activeChatId, setActiveChatId] = useState(bootstrap.id);
  const [chatsReady, setChatsReady] = useState(false);
  const [health, setHealth] = useState<{ openai_configured?: boolean; groq_configured?: boolean } | null>(null);
  const [uploads, setUploads] = useState<{ name: string; path: string; bytes: number }[]>([]);
  const [builtin, setBuiltin] = useState<{ name: string; path: string; bytes: number }[]>([]);
  const [uploading, setUploading] = useState(false);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const composerRef = useRef<HTMLTextAreaElement>(null);
  const threadEndRef = useRef<HTMLDivElement>(null);

  const selected = useMemo(() => models.find((item) => `${item.provider}:${item.model_id}` === modelId), [models, modelId]);
  const activeChat = chats.find((chat) => chat.id === activeChatId) ?? chats[0];
  const turns = activeChat?.turns ?? [];
  const liveTurn = turns.find((turn) => turn.status === "running" || turn.status === "queued");
  const running = Boolean(liveTurn);
  const listedChats = chats.filter((chat) => chat.turns.length || chat.id === activeChatId);

  useEffect(() => {
    if (!chatsReady) return;
    const payload = {
      activeChatId,
      chats: chats
        .filter((chat) => chat.turns.length)
        .map((chat) => ({
          id: chat.id,
          title: displayTitle(chat),
          named: Boolean(chat.named),
          turns: chat.turns.map((turn) => ({ id: turn.executionId, prompt: turn.prompt })),
        })),
    };
    if (!payload.chats.length) {
      localStorage.removeItem(CHAT_STORAGE_KEY);
      return;
    }
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(payload));
  }, [chats, activeChatId, chatsReady]);

  useEffect(() => {
    api.models().then((data) => {
      setModels(data.models);
      if (data.models[0]) setModelId(`${data.models[0].provider}:${data.models[0].model_id}`);
    }).catch((err) => setError(err.message));
    api.health().then(setHealth).catch(() => undefined);
    api.uploads()
      .then((data) => {
        setUploads(data.uploads || data.files);
        setBuiltin(data.builtin || []);
      })
      .catch(() => undefined);

    const stored = loadStoredChats();

    async function hydrateTurn(id: string, fallback?: AgentTurnData, promptHint?: string): Promise<AgentTurnData | null> {
      try {
        const detail = await api.events(id);
        return {
          executionId: id,
          prompt:
            fallback?.prompt ||
            promptHint ||
            detail.fingerprint?.task_text ||
            detail.fingerprint?.task_preview ||
            "Task",
          status: detail.status || fallback?.status || "completed",
          events: detail.events,
          finalOutput: detail.final_output ?? fallback?.finalOutput ?? null,
          fingerprint: detail.fingerprint || fallback?.fingerprint || null,
          startedAt: fallback?.startedAt,
        };
      } catch {
        return fallback ?? null;
      }
    }

    (async () => {
      try {
        const restored: ChatSession[] = [];
        if (stored) {
          for (const item of stored.chats) {
            const loaded = (
              await Promise.all(storedTurns(item).map((turn) => hydrateTurn(turn.id, undefined, turn.prompt)))
            ).filter((turn): turn is AgentTurnData => Boolean(turn));
            if (!loaded.length) continue;
            restored.push({
            id: item.id,
            title: item.title || titleFromTurns(loaded),
            named: Boolean(item.named && item.title),
            turns: loaded,
          });
          }
        }

        let live: HistoryRow | undefined;
        try {
          const history = await api.history("");
          live = history.executions.find((row) => row.status === "running" || row.status === "queued");
        } catch {
          live = undefined;
        }

        setChats((current) => {
          if (current.some((chat) => chat.turns.length)) return current;
          if (restored.length) {
            const hasLive = live && restored.some((chat) => chat.turns.some((turn) => turn.executionId === live.execution_id));
            if (live && !hasLive) {
              return [{ id: restored[0].id, title: restored[0].title, turns: [fromHistory(live), ...restored[0].turns] }, ...restored.slice(1)];
            }
            return restored;
          }
          if (live) {
            return [{ ...current[0], title: titleFromTurns([fromHistory(live)]), turns: [fromHistory(live)] }];
          }
          return current;
        });
        if (stored?.activeChatId) {
          setActiveChatId((current) => {
            if (restored.some((chat) => chat.id === stored.activeChatId)) return stored.activeChatId;
            return restored[0]?.id || current;
          });
        }
        if (live) {
          const detail = await hydrateTurn(live.execution_id, fromHistory(live));
          if (detail) {
            setChats((current) =>
              current.map((chat) => ({
                ...chat,
                turns: chat.turns.map((turn) => (turn.executionId === live.execution_id ? detail : turn)),
              })),
            );
          }
        }
      } finally {
        setChatsReady(true);
      }
    })();
  }, []);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, liveTurn?.executionId]);

  const liveIds = useMemo(
    () =>
      chats
        .flatMap((chat) => chat.turns)
        .filter((turn) => turn.status === "running" || turn.status === "queued")
        .map((turn) => turn.executionId),
    [chats],
  );
  const liveKey = liveIds.join(",");

  useEffect(() => {
    if (!liveKey) return;
    const ids = liveKey.split(",");
    let cancelled = false;
    const poll = async () => {
      try {
        const updates = await Promise.all(ids.map((id) => api.events(id)));
        if (cancelled) return;
        setChats((current) =>
          current.map((chat) => ({
            ...chat,
            turns: chat.turns.map((turn) => {
              const data = updates.find((_, index) => ids[index] === turn.executionId);
              if (!data) return turn;
              return {
                ...turn,
                status: data.status,
                events: data.events,
                finalOutput: data.final_output,
                fingerprint: data.fingerprint,
              };
            }),
          })),
        );
        const stillLive = updates.some((data) => data.status === "running" || data.status === "queued");
        if (stillLive) window.setTimeout(poll, 900);
        else setStopping(false);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Polling failed");
          setStopping(false);
        }
      }
    };
    poll();
    return () => {
      cancelled = true;
    };
  }, [liveKey]);

  async function onRun(event: FormEvent) {
    event.preventDefault();
    if (!selected || !task.trim()) return;
    const prompt = task.trim();
    setError(null);
    try {
      const result = await api.startExecution({
        task: prompt,
        model: { provider: selected.provider, model_id: selected.model_id },
        task_type: ragEnabled ? "rag" : "general",
        comparison_group_id: null,
        rag_enabled: ragEnabled,
        workspace_id: "demo-workspace",
      });
      const nextTurn: AgentTurnData = {
        executionId: result.execution_id,
        prompt,
        status: "running",
        events: [],
        finalOutput: null,
        fingerprint: null,
        startedAt: new Date().toISOString(),
      };
      setChats((current) =>
        current.map((chat) => {
          if (chat.id !== activeChatId) return chat;
          const turnsNext = [...chat.turns.filter((turn) => turn.executionId !== result.execution_id), nextTurn];
          return { ...chat, title: chat.named ? chat.title : titleFromTurns(turnsNext, chat.title), turns: turnsNext };
        }),
      );
      setTask("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start execution");
    }
  }

  async function onStop() {
    if (!liveTurn || stopping) return;
    setStopping(true);
    setError(null);
    try {
      await api.stopExecution(liveTurn.executionId);
    } catch {
      setChats((current) =>
        current.map((chat) => ({
          ...chat,
          turns: chat.turns.map((turn) =>
            turn.executionId === liveTurn.executionId
              ? { ...turn, status: "cancelled", finalOutput: turn.finalOutput || "Stopped by user." }
              : turn,
          ),
        })),
      );
      setStopping(false);
    }
  }

  function reusePrompt(prompt: string) {
    setTask(prompt);
    composerRef.current?.focus();
    composerRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function onNewChat() {
    if (!turns.length && !task && !error) return;
    const next = createChat();
    setChats((current) => {
      const saved = current.map((chat) =>
        chat.id === activeChatId
          ? { ...chat, title: chat.named ? chat.title : titleFromTurns(chat.turns, chat.title) }
          : chat,
      );
      if (!turns.length) return saved;
      return [next, ...saved.filter((chat) => chat.turns.length || chat.id === activeChatId)];
    });
    if (turns.length) setActiveChatId(next.id);
    setStopping(false);
    setError(null);
    setTask("");
    composerRef.current?.focus();
  }

  function openChat(id: string) {
    setActiveChatId(id);
    setError(null);
    setStopping(false);
    setRenamingId(null);
  }

  function deleteChat(chat: ChatSession) {
    if (chat.turns.length && !window.confirm(`Delete "${displayTitle(chat)}"? The runs stay in Observability.`)) return;
    const remaining = chats.filter((item) => item.id !== chat.id);
    const next = remaining.length ? remaining : [createChat()];
    setChats(next);
    if (chat.id === activeChatId) setActiveChatId(next[0].id);
    setRenamingId(null);
    setStopping(false);
    setError(null);
  }

  function startRename(chat: ChatSession) {
    setRenamingId(chat.id);
    setRenameDraft(displayTitle(chat));
  }

  function commitRename(id: string) {
    const next = renameDraft.trim();
    setChats((current) =>
      current.map((chat) => {
        if (chat.id !== id) return chat;
        if (!next) return { ...chat, named: false, title: titleFromTurns(chat.turns, "New chat") };
        return { ...chat, named: true, title: next };
      }),
    );
    setRenamingId(null);
  }

  async function loadTrace(id: string) {
    try {
      const data = await api.events(id);
      setChats((current) =>
        current.map((chat) => ({
          ...chat,
          turns: chat.turns.map((turn) =>
            turn.executionId === id
              ? { ...turn, events: data.events, finalOutput: data.final_output ?? turn.finalOutput, fingerprint: data.fingerprint }
              : turn,
          ),
        })),
      );
    } catch {
      setError("Could not load execution steps.");
    }
  }

  return (
    <div className="grid min-h-[calc(100vh-61px)] grid-cols-1 lg:grid-cols-[minmax(0,260px)_minmax(0,1fr)]">
      <aside className="min-w-0 overflow-hidden border-b border-[var(--border)] bg-[var(--panel)] p-4 lg:border-b-0 lg:border-r">
        <button
          type="button"
          onClick={onNewChat}
          disabled={!turns.length && !task && !error}
          className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-left text-sm text-white hover:border-[var(--accent)] disabled:opacity-40"
        >
          New chat
        </button>
        <p className="mt-1 text-[11px] text-[var(--muted)]">Starts a blank page. Previous chats stay here; the model does not use them as memory.</p>
        {listedChats.length ? (
          <>
            <div className="mt-6 text-xs uppercase tracking-wide text-[var(--muted)]">Chats</div>
            <div className="mt-2 space-y-2">
              {listedChats.map((chat) => (
                <div
                  key={chat.id}
                  className={`rounded-lg border p-2 ${
                    chat.id === activeChatId
                      ? "border-[var(--accent)] bg-[var(--bg)]"
                      : "border-[var(--border)] bg-[var(--bg)]"
                  }`}
                >
                  {renamingId === chat.id ? (
                    <input
                      autoFocus
                      value={renameDraft}
                      onChange={(event) => setRenameDraft(event.target.value)}
                      onBlur={() => commitRename(chat.id)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") {
                          event.preventDefault();
                          commitRename(chat.id);
                        }
                        if (event.key === "Escape") setRenamingId(null);
                      }}
                      className="w-full rounded border border-[var(--accent)] bg-[var(--panel)] px-1.5 py-1 text-xs text-white outline-none"
                    />
                  ) : (
                    <button
                      type="button"
                      className={`block w-full text-left text-xs hover:text-white ${
                        chat.id === activeChatId ? "text-white" : "text-[var(--muted)]"
                      }`}
                      onClick={() => openChat(chat.id)}
                    >
                      <div className="line-clamp-2">{displayTitle(chat)}</div>
                    </button>
                  )}
                  <div className="mt-1 flex items-center justify-between gap-2">
                    <div className="text-[11px] text-[var(--muted)]">
                      {chat.turns.length ? `${chat.turns.length} run${chat.turns.length === 1 ? "" : "s"}` : "Empty"}
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        className="text-[11px] text-[var(--accent-2)] hover:text-white"
                        onClick={() => startRename(chat)}
                      >
                        Rename
                      </button>
                      <button
                        type="button"
                        className="text-[11px] text-[var(--muted)] hover:text-[var(--error)]"
                        onClick={() => deleteChat(chat)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
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
            <p className="text-sm text-[var(--muted)]">Give the agent a task to start an execution. New chat opens a blank page; open a previous chat from the sidebar to see its prompt, answer, and tools. Each run is independent.</p>
          ) : (
            <div className="space-y-8">
              {turns.length ? (
                <div className="flex items-center justify-between gap-3">
                  <p className="text-xs text-[var(--muted)]">
                    This chat is a log, not memory. Each run is independent.
                  </p>
                  <button
                    type="button"
                    onClick={onNewChat}
                    className="shrink-0 rounded-md border border-[var(--border)] px-3 py-1 text-xs text-white hover:border-[var(--accent)]"
                  >
                    New chat
                  </button>
                </div>
              ) : null}
              {turns.map((turn) => (
                <AgentTurn
                  key={turn.executionId}
                  turn={turn}
                  live={turn.executionId === liveTurn?.executionId}
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
                      setUploads(listed.uploads || listed.files);
                      setBuiltin(listed.builtin || []);
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
            <KnowledgeFilesPanel
              uploads={uploads}
              builtin={builtin}
              onChange={(next) => {
                setUploads(next.uploads);
                setBuiltin(next.builtin);
              }}
              onError={setError}
            />
            {uploading ? <span className="text-xs text-[var(--muted)]">Indexing…</span> : null}
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
