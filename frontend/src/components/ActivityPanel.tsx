import { useEffect, useMemo, useRef, useState } from "react";
import type { ExecutionEvent } from "../types";
import { ExecutionTrace } from "./ExecutionTrace";

const COLLAPSE_AFTER = 5;

const WORK_EVENTS = new Set([
  "llm_started",
  "llm_completed",
  "tool_started",
  "tool_completed",
  "retry",
  "rag_started",
  "rag_completed",
  "file_edit",
]);

function toolPhrase(name: string): string {
  switch (name) {
    case "rag_search":
      return "Searching knowledge";
    case "read_file":
      return "Reading files";
    case "list_files":
      return "Listing files";
    case "search_files":
      return "Searching files";
    case "write_file":
      return "Editing files";
    case "run_command":
      return "Running command";
    case "run_tests":
      return "Running tests";
    case "preview_csv":
      return "Reading CSV";
    default:
      return name ? `Using ${name}` : "Using tools";
  }
}

function currentActivity(events: ExecutionEvent[]): string {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index];
    if (event.event_type === "llm_started") return "Calling model";
    if (event.event_type === "rag_started") return "Searching knowledge";
    if (event.event_type === "file_edit") return "Editing files";
    if (event.event_type === "tool_started") {
      return toolPhrase(String(event.metadata?.tool_name || ""));
    }
    if (event.event_type === "llm_completed") return "Writing answer";
    if (event.event_type === "tool_completed" || event.event_type === "retry") {
      return toolPhrase(String(event.metadata?.tool_name || ""));
    }
  }
  return "Working";
}

function usedTools(events: ExecutionEvent[]): string[] {
  const names: string[] = [];
  for (const event of events) {
    if (event.event_type !== "tool_started") continue;
    const name = String(event.metadata?.tool_name || "");
    if (name && !names.includes(name)) names.push(name);
  }
  return names;
}

function workCounts(events: ExecutionEvent[]) {
  const llm = events.filter((event) => event.event_type === "llm_started").length;
  const tools = events.filter((event) => event.event_type === "tool_started").length;
  return { llm, tools, steps: llm + tools };
}

export function ActivityPanel({
  events,
  live,
  onExpandEmpty,
}: {
  events: ExecutionEvent[];
  live?: boolean;
  onExpandEmpty?: () => void;
}) {
  const counts = useMemo(() => workCounts(events), [events]);
  const tools = useMemo(() => usedTools(events), [events]);
  const visible = useMemo(() => events.filter((event) => WORK_EVENTS.has(event.event_type)), [events]);
  const [expanded, setExpanded] = useState(() => Boolean(live) && counts.steps <= COLLAPSE_AFTER);
  const autoCollapsed = useRef(false);

  useEffect(() => {
    if (live && counts.steps > COLLAPSE_AFTER && !autoCollapsed.current) {
      autoCollapsed.current = true;
      setExpanded(false);
    }
  }, [live, counts.steps]);

  if (!live && !events.length && !counts.steps) return null;

  const title = live ? currentActivity(events) : "Activity";
  const summary = [
    counts.llm ? `${counts.llm} LLM` : null,
    counts.tools ? `${counts.tools} tools` : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="overflow-hidden rounded-xl border border-[var(--border)] bg-[var(--panel)]">
      <button
        type="button"
        className="flex w-full items-center gap-3 px-4 py-2.5 text-left"
        onClick={() => {
          const next = !expanded;
          setExpanded(next);
          if (next && events.length === 0) onExpandEmpty?.();
        }}
      >
        <span
          className={`h-2 w-2 shrink-0 rounded-full ${
            live ? "animate-pulse bg-[var(--accent)]" : "bg-[var(--muted)]"
          }`}
        />
        <span className="min-w-0 flex-1 truncate text-sm">
          {title}
          {summary ? <span className="text-[var(--muted)]"> · {summary}</span> : null}
        </span>
        <span className="shrink-0 text-xs text-[var(--muted)]">{expanded ? "Hide" : "Show"}</span>
      </button>
      {!expanded && tools.length ? (
        <div className="truncate px-4 pb-2.5 pl-9 text-xs text-[var(--muted)]" title={tools.join(", ")}>
          {tools.join(" · ")}
        </div>
      ) : null}
      {expanded ? (
        <div className="max-h-48 overflow-auto border-t border-[var(--border)] px-4 py-3">
          <ExecutionTrace events={visible.length ? visible : events} />
        </div>
      ) : null}
    </div>
  );
}
