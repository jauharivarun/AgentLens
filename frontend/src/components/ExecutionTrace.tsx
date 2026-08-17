import type { ExecutionEvent } from "../types";
import { useState } from "react";

function eventColor(type: string) {
  if (type.includes("fail")) return "bg-[var(--error)]";
  if (type.startsWith("tool")) return "bg-[var(--warning)]";
  if (type.startsWith("llm")) return "bg-[var(--accent)]";
  if (type.startsWith("rag")) return "bg-[#5eead4]";
  if (type === "file_edit") return "bg-[var(--success)]";
  return "bg-[var(--muted)]";
}

function eventLabel(type: string): string {
  switch (type) {
    case "execution_started":
      return "Started";
    case "user_message":
      return "Task";
    case "llm_started":
      return "Model";
    case "llm_completed":
      return "Model";
    case "tool_started":
      return "Tool";
    case "tool_completed":
    case "retry":
      return "Tool";
    case "rag_started":
    case "rag_completed":
      return "RAG";
    case "file_edit":
      return "Edit";
    case "execution_completed":
      return "Done";
    case "execution_cancelled":
      return "Stopped";
    case "execution_failed":
      return "Failed";
    default:
      return type.replaceAll("_", " ");
  }
}

export function ExecutionTrace({ events }: { events: ExecutionEvent[] }) {
  const [openId, setOpenId] = useState<string | null>(null);
  if (!events.length) {
    return <div className="text-sm text-[var(--muted)]">Waiting for execution events…</div>;
  }
  return (
    <ol className="ml-1 border-l border-[var(--border)] pl-4">
      {events.map((event) => {
        const open = openId === event.id;
        const hasMeta = Boolean(event.metadata && Object.keys(event.metadata).length);
        return (
          <li key={event.id} className="relative pb-3 last:pb-0">
            <span
              className={`absolute -left-[21px] top-1.5 h-2 w-2 rounded-full ${eventColor(event.event_type)}`}
            />
            <button
              type="button"
              onClick={() => hasMeta && setOpenId(open ? null : event.id)}
              className={`w-full text-left ${hasMeta ? "cursor-pointer" : "cursor-default"}`}
            >
              <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                <span className="mono text-[11px] uppercase tracking-wide text-[var(--muted)]">
                  {eventLabel(event.event_type)}
                </span>
                <span className="text-sm text-[var(--text)]">{event.summary}</span>
              </div>
            </button>
            {open && event.metadata ? (
              <pre className="mt-1 pl-0 text-[11px] leading-5 text-[var(--muted)]">
                {JSON.stringify(event.metadata, null, 2)}
              </pre>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}
