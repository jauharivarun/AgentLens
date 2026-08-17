import { Link } from "react-router-dom";
import type { ExecutionEvent, Fingerprint } from "../types";
import { ActivityPanel } from "./ActivityPanel";
import { ExecutionFingerprint } from "./ExecutionFingerprint";
import { MarkdownText } from "./MarkdownText";

export type AgentTurnData = {
  executionId: string;
  prompt: string;
  status: string;
  events: ExecutionEvent[];
  finalOutput: string | null;
  fingerprint: Fingerprint | null;
  startedAt?: string;
};

export function AgentTurn({
  turn,
  live,
  onReuse,
  onToggleTrace,
}: {
  turn: AgentTurnData;
  live?: boolean;
  onReuse: (prompt: string) => void;
  onToggleTrace?: (executionId: string) => void;
}) {
  const running = turn.status === "running" || turn.status === "queued";
  const time = turn.startedAt?.slice(11, 19);

  return (
    <article id={`turn-${turn.executionId}`} className="space-y-3">
      <div className="rounded-xl border border-[var(--border)] bg-[var(--panel-2)] p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="text-xs uppercase tracking-wide text-[var(--muted)]">You asked</div>
          <div className="flex items-center gap-2">
            {time ? <span className="mono text-[11px] text-[var(--muted)]">{time}</span> : null}
            <button
              type="button"
              className="text-xs text-[var(--accent-2)] hover:text-white"
              onClick={() => onReuse(turn.prompt)}
            >
              Reuse prompt
            </button>
          </div>
        </div>
        <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{turn.prompt}</p>
      </div>

      <ActivityPanel
        events={turn.events}
        live={Boolean(live || running)}
        onExpandEmpty={() => onToggleTrace?.(turn.executionId)}
      />

      {turn.finalOutput ? (
        <div className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="text-xs uppercase tracking-wide text-[var(--muted)]">Final response</div>
            {turn.fingerprint?.model ? (
              <span className="text-xs text-[var(--muted)]">{turn.fingerprint.model}</span>
            ) : null}
          </div>
          <div className="mt-2">
            <MarkdownText text={turn.finalOutput} />
          </div>
        </div>
      ) : running ? (
        <div className="rounded-xl border border-dashed border-[var(--border)] px-4 py-3 text-sm text-[var(--muted)]">
          Waiting for the final response…
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-3">
        <ExecutionFingerprint fingerprint={turn.fingerprint} variant="inline" />
        {!running ? (
          <Link className="text-xs text-[var(--accent-2)]" to={`/observability?execution=${turn.executionId}`}>
            View in Observability
          </Link>
        ) : null}
      </div>
    </article>
  );
}
