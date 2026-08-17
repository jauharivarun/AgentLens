import type { Fingerprint } from "../types";
import { formatDuration, formatNumber, formatUsd } from "../lib/format";

export function ExecutionFingerprint({
  fingerprint,
  variant = "card",
}: {
  fingerprint: Fingerprint | null;
  variant?: "card" | "inline";
}) {
  if (!fingerprint) return null;
  const stats = (
    <>
      {fingerprint.llm_calls} LLM · {fingerprint.tool_calls} tools · {fingerprint.files_touched} files ·{" "}
      {formatNumber(fingerprint.input_tokens)} in / {formatNumber(fingerprint.output_tokens)} out ·{" "}
      {formatDuration(fingerprint.duration_ms)} elapsed · {formatUsd(fingerprint.estimated_cost_usd)}
    </>
  );
  if (variant === "inline") {
    return (
      <p className="text-xs text-[var(--muted)]">
        {fingerprint.model} · {fingerprint.outcome || fingerprint.status} · {stats}
      </p>
    );
  }
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4">
      <div className="text-xs uppercase tracking-wide text-[var(--muted)]">Execution fingerprint</div>
      <div className="mt-2 font-medium">{fingerprint.model}</div>
      <div className="text-sm text-[var(--muted)]">
        {fingerprint.task_type} · {fingerprint.outcome || fingerprint.status}
      </div>
      <div className="mt-3 text-xs text-[var(--muted)]">{stats}</div>
    </div>
  );
}
