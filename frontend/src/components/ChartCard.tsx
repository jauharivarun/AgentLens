import type { ReactElement } from "react";
import { ResponsiveContainer } from "recharts";

const CHART_TEXT = "#e8edf5";

export const chartTooltipStyle = {
  background: "#171b22",
  border: "1px solid #232833",
  borderRadius: 8,
  fontSize: 12,
  color: CHART_TEXT,
};

export const chartTooltipItemStyle = { color: CHART_TEXT };
export const chartTooltipLabelStyle = { color: CHART_TEXT };
export const chartLegendStyle = { color: "#c5cdd9", fontSize: 12 };

export const chartTooltipProps = {
  contentStyle: chartTooltipStyle,
  itemStyle: chartTooltipItemStyle,
  labelStyle: chartTooltipLabelStyle,
};

export function ChartCard({
  title,
  children,
  empty,
}: {
  title: string;
  children: ReactElement;
  empty?: boolean;
}) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4">
      <h2 className="text-sm font-medium">{title}</h2>
      <p className="mb-3 text-xs text-[var(--muted)]">Based on your observed runs.</p>
      {empty ? (
        <div className="flex h-56 items-center text-sm text-[var(--muted)]">No data for this chart yet.</div>
      ) : (
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            {children}
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export function chartLabel(value: unknown, kind: "number" | "usd" | "ms" | "pct" = "number"): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  const num = Number(value);
  if (kind === "usd") {
    if (num === 0) return "$0.00";
    if (num < 0.01) return `$${num.toFixed(4)}`;
    return `$${num.toFixed(3)}`;
  }
  if (kind === "ms") {
    if (num < 1000) return `${Math.round(num)}ms`;
    return `${(num / 1000).toFixed(1)}s`;
  }
  if (kind === "pct") return `${(num * 100).toFixed(1)}%`;
  return Math.round(num).toLocaleString();
}
