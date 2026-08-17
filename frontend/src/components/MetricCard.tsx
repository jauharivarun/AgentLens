type Props = {
  label: string;
  value: string;
  hint?: string;
  source?: string;
};

export function MetricCard({ label, value, hint, source }: Props) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4" title={hint}>
      <div className="mono text-2xl font-medium">{value}</div>
      <div className="mt-1 text-xs uppercase tracking-wide text-[var(--muted)]">{label}</div>
      {source ? <div className="mt-2 text-[10px] text-[var(--muted)]">{source}</div> : null}
    </div>
  );
}
