export function formatNumber(value: number | null | undefined, digits = 0): string {
  if (value === null || value === undefined) return "N/A";
  return value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

export function formatUsd(value: number | null | undefined): string {
  if (value === null || value === undefined) return "N/A";
  if (value === 0) return "$0.00";
  if (value < 0.01) return `$${value.toFixed(4)}`;
  return `$${value.toFixed(3)}`;
}

export function formatDuration(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return "N/A";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export function formatPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return "N/A";
  return `${(value * 100).toFixed(1)}%`;
}

export function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "N/A";
  if (typeof value === "number") return formatNumber(value, 2);
  return String(value);
}

const PROVIDER_LABELS: Record<string, string> = {
  openai: "OpenAI",
  groq: "Groq",
};

export function formatProvider(provider: string): string {
  return PROVIDER_LABELS[provider] || provider;
}

export function formatModelLabel(provider: string, displayName: string): string {
  return `${formatProvider(provider)} / ${displayName}`;
}
