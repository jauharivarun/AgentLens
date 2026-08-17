import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client";
import { ChartCard, chartLabel, chartLegendStyle, chartTooltipProps } from "../components/ChartCard";
import { ExecutionFingerprint } from "../components/ExecutionFingerprint";
import { ExecutionTrace } from "../components/ExecutionTrace";
import { MetricCard } from "../components/MetricCard";
import { formatDuration, formatModelLabel, formatNumber, formatPct, formatUsd } from "../lib/format";
import type { ExecutionDetail, HistoryRow, ModelOption, ModelProfile, Overview, ToolRow } from "../types";

const EMPTY = "Run your first task to populate observability.";
const PIE_COLORS = ["#7c8cff", "#5eead4", "#f5c542", "#ff6b6b", "#3dd68c", "#9aa5ff", "#c084fc"];

function shortRunLabel(row: HistoryRow, index: number): string {
  const clock = row.started_at?.slice(11, 16);
  return clock || `R${index + 1}`;
}

export function ObservabilityPage() {
  const [params, setParams] = useSearchParams();
  const selectedExecution = params.get("execution");
  const [models, setModels] = useState<ModelOption[]>([]);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [profiles, setProfiles] = useState<ModelProfile[]>([]);
  const [tools, setTools] = useState<ToolRow[]>([]);
  const [history, setHistory] = useState<HistoryRow[]>([]);
  const [detail, setDetail] = useState<ExecutionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({
    model: "",
    outcome: "",
    rag_enabled: "",
    has_retries: "",
  });

  const query = useMemo(() => {
    const search = new URLSearchParams();
    if (filters.model) {
      const separator = filters.model.indexOf(":");
      const provider = filters.model.slice(0, separator);
      const model = filters.model.slice(separator + 1);
      search.set("provider", provider);
      search.set("model", model);
    }
    if (filters.outcome) search.set("outcome", filters.outcome);
    if (filters.rag_enabled === "true") search.set("rag_enabled", "true");
    if (filters.has_retries === "true") search.set("has_retries", "true");
    const text = search.toString();
    return text ? `?${text}` : "";
  }, [filters]);

  useEffect(() => {
    api.models().then((data) => setModels(data.models)).catch(() => undefined);
  }, []);

  useEffect(() => {
    setError(null);
    Promise.all([
      api.overview(query),
      api.modelAnalytics(query),
      api.toolAnalytics(query),
      api.history(query),
    ])
      .then(([overviewData, modelData, toolData, historyData]) => {
        setOverview(overviewData);
        setProfiles(modelData.models);
        setTools(toolData.tools);
        setHistory(historyData.executions);
      })
      .catch((err) => setError(err.message));
  }, [query]);

  useEffect(() => {
    if (!selectedExecution) {
      setDetail(null);
      return;
    }
    api.execution(selectedExecution).then(setDetail).catch((err) => setError(err.message));
  }, [selectedExecution]);

  const empty = (overview?.executions || 0) === 0;

  const timeSeries = useMemo(() => {
    const chronological = [...history].sort((a, b) => (a.started_at || "").localeCompare(b.started_at || ""));
    return chronological.slice(-20).map((row, index) => ({
      name: shortRunLabel(row, index),
      tokens: row.total_tokens,
      llm: row.llm_calls,
      tools: row.tool_calls,
    }));
  }, [history]);

  const modelDuration = useMemo(
    () =>
      profiles.map((item) => ({
        name: item.display_label || formatModelLabel(item.provider, item.display_name || item.model_id),
        duration: item.median_duration_ms,
      })),
    [profiles],
  );

  const modelScatter = useMemo(
    () =>
      profiles.flatMap((item) => {
        const tokens = item.average_tokens;
        const duration = item.median_duration_ms;
        if (tokens == null || duration == null || Number.isNaN(tokens) || Number.isNaN(duration)) return [];
        return [
          {
            name: item.display_label || formatModelLabel(item.provider, item.display_name || item.model_id),
            tokens,
            duration,
            runs: item.runs,
          },
        ];
      }),
    [profiles],
  );

  const toolMix = useMemo(
    () => tools.map((tool) => ({ name: tool.tool_name, value: tool.calls })),
    [tools],
  );

  const toolLatency = useMemo(
    () =>
      tools.map((tool) => ({
        name: tool.tool_name,
        latency: tool.median_latency_ms,
      })),
    [tools],
  );

  return (
    <div className="space-y-6 p-5">
      <div>
        <h1 className="text-xl font-semibold">Observability</h1>
        <p className="mt-1 text-sm text-[var(--muted)]">
          Raw token counts are not directly comparable across different workloads. Compare runs that used the same prompt and conditions.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <select className="rounded-md border border-[var(--border)] bg-[var(--panel)] px-2 py-1 text-sm" value={filters.model} onChange={(e) => setFilters({ ...filters, model: e.target.value })}>
          <option value="">All models</option>
          {models.map((model) => (
            <option key={`${model.provider}:${model.model_id}`} value={`${model.provider}:${model.model_id}`}>
              {formatModelLabel(model.provider, model.display_name)}
            </option>
          ))}
        </select>
        <select className="rounded-md border border-[var(--border)] bg-[var(--panel)] px-2 py-1 text-sm" value={filters.outcome} onChange={(e) => setFilters({ ...filters, outcome: e.target.value })}>
          <option value="">All outcomes</option>
          <option value="success">Success</option>
          <option value="failed">Failed</option>
          <option value="partial">Partial</option>
          <option value="cancelled">Stopped</option>
        </select>
        <label className="flex items-center gap-2 text-xs text-[var(--muted)]">
          <input type="checkbox" checked={filters.rag_enabled === "true"} onChange={(e) => setFilters({ ...filters, rag_enabled: e.target.checked ? "true" : "" })} />
          RAG only
        </label>
        <label className="flex items-center gap-2 text-xs text-[var(--muted)]">
          <input type="checkbox" checked={filters.has_retries === "true"} onChange={(e) => setFilters({ ...filters, has_retries: e.target.checked ? "true" : "" })} />
          Has retries
        </label>
      </div>

      {error ? <div className="rounded-lg border border-[var(--error)]/40 bg-[var(--error)]/10 px-3 py-2 text-sm">{error}</div> : null}

      {empty ? (
        <div className="rounded-xl border border-dashed border-[var(--border)] p-8 text-[var(--muted)]">
          {EMPTY}
          <div className="mt-3">
            <Link className="text-[var(--accent-2)]" to="/">
              Go to Agent
            </Link>
          </div>
        </div>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Executions" value={formatNumber(overview?.executions ?? 0)} source="Runtime measured" />
            <MetricCard label="LLM calls" value={formatNumber(overview?.llm_calls ?? 0)} source="Runtime measured" />
            <MetricCard label="Total tokens" value={formatNumber(overview?.total_tokens)} hint="Provider reported when available" source="Provider reported" />
            <MetricCard label="Estimated cost" value={formatUsd(overview?.estimated_cost_usd)} source="Calculated" />
            <MetricCard label="Median duration" value={formatDuration(overview?.median_duration_ms)} source="Runtime measured" />
            <MetricCard label="Tool success" value={formatPct(overview?.tool_success_rate)} source="Runtime measured" />
            <MetricCard label="Pricing coverage" value={formatPct(overview?.pricing_coverage)} source="Calculated" />
          </div>

          <h2 className="text-sm font-medium text-[var(--muted)]">Over time</h2>
          <section className="grid gap-4 xl:grid-cols-2">
            <ChartCard title="Tokens per run" empty={!timeSeries.length}>
              <LineChart data={timeSeries}>
                <CartesianGrid stroke="#232833" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#8b95a7" fontSize={11} />
                <YAxis stroke="#8b95a7" fontSize={11} />
                <Tooltip {...chartTooltipProps} formatter={(value) => chartLabel(value, "number")} />
                <Line type="monotone" dataKey="tokens" name="Tokens" stroke="#7c8cff" dot connectNulls={false} />
              </LineChart>
            </ChartCard>
            <ChartCard title="LLM vs tool calls per run" empty={!timeSeries.length}>
              <LineChart data={timeSeries}>
                <CartesianGrid stroke="#232833" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#8b95a7" fontSize={11} />
                <YAxis stroke="#8b95a7" fontSize={11} allowDecimals={false} />
                <Tooltip {...chartTooltipProps} formatter={(value) => chartLabel(value, "number")} />
                <Legend wrapperStyle={chartLegendStyle} />
                <Line type="monotone" dataKey="llm" name="LLM" stroke="#7c8cff" dot />
                <Line type="monotone" dataKey="tools" name="Tools" stroke="#f5c542" dot />
              </LineChart>
            </ChartCard>
          </section>

          <h2 className="text-sm font-medium text-[var(--muted)]">By model</h2>
          <section className="grid gap-4 xl:grid-cols-2">
            <ChartCard title="Median duration by model" empty={!modelDuration.length}>
              <BarChart data={modelDuration}>
                <CartesianGrid stroke="#232833" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#8b95a7" fontSize={11} />
                <YAxis stroke="#8b95a7" fontSize={11} />
                <Tooltip {...chartTooltipProps} formatter={(value) => chartLabel(value, "ms")} />
                <Bar dataKey="duration" name="Duration" fill="#f5c542" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ChartCard>
            <ChartCard title="Tokens vs duration" empty={!modelScatter.length}>
              <ScatterChart margin={{ top: 8, right: 12, bottom: 8, left: 4 }}>
                <CartesianGrid stroke="#232833" strokeDasharray="3 3" />
                <XAxis
                  dataKey="tokens"
                  name="Tokens"
                  type="number"
                  stroke="#8b95a7"
                  fontSize={11}
                  tickFormatter={(value) => chartLabel(value, "number")}
                />
                <YAxis
                  dataKey="duration"
                  name="Duration"
                  type="number"
                  stroke="#8b95a7"
                  fontSize={11}
                  tickFormatter={(value) => chartLabel(value, "ms")}
                />
                <Tooltip
                  {...chartTooltipProps}
                  cursor={{ stroke: "#8b95a7", strokeDasharray: "3 3" }}
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const point = payload[0].payload as { name: string; tokens: number; duration: number; runs: number };
                    return (
                      <div className="px-3 py-2" style={chartTooltipProps.contentStyle}>
                        <div className="mb-1 font-medium">{point.name}</div>
                        <div>Tokens: {chartLabel(point.tokens, "number")}</div>
                        <div>Duration: {chartLabel(point.duration, "ms")}</div>
                        <div>Runs: {chartLabel(point.runs, "number")}</div>
                      </div>
                    );
                  }}
                />
                <Scatter
                  data={modelScatter}
                  name="Models"
                  shape={(props) => {
                    const { cx, cy, fill } = props;
                    if (cx == null || cy == null) return null;
                    return <circle cx={cx} cy={cy} r={7} fill={fill} stroke="#e8edf5" strokeWidth={1.5} />;
                  }}
                >
                  {modelScatter.map((entry, index) => (
                    <Cell key={entry.name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ChartCard>
          </section>

          <h2 className="text-sm font-medium text-[var(--muted)]">Tools</h2>
          <section className="grid gap-4 xl:grid-cols-2">
            <ChartCard title="Tool call mix" empty={!toolMix.length}>
              <PieChart>
                <Pie data={toolMix} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={42} outerRadius={80} paddingAngle={2}>
                  {toolMix.map((entry, index) => (
                    <Cell key={entry.name} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip {...chartTooltipProps} formatter={(value) => chartLabel(value, "number")} />
                <Legend wrapperStyle={chartLegendStyle} />
              </PieChart>
            </ChartCard>
            <ChartCard title="Median tool latency" empty={!toolLatency.length}>
              <BarChart data={toolLatency}>
                <CartesianGrid stroke="#232833" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#8b95a7" fontSize={11} />
                <YAxis stroke="#8b95a7" fontSize={11} />
                <Tooltip {...chartTooltipProps} formatter={(value) => chartLabel(value, "ms")} />
                <Bar dataKey="latency" name="Latency" fill="#9aa5ff" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ChartCard>
          </section>

          <section className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4">
            <h2 className="text-sm font-medium">Model efficiency profile</h2>
            <p className="mb-3 text-xs text-[var(--muted)]">Based on your observed runs. Not a universal benchmark.</p>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] text-left text-sm">
                <thead className="text-xs uppercase text-[var(--muted)]">
                  <tr>
                    <th className="py-2">Model</th>
                    <th>Runs</th>
                    <th>Observed success</th>
                    <th>Median time</th>
                    <th>Avg tokens</th>
                    <th>Avg cost</th>
                    <th>Tool success</th>
                  </tr>
                </thead>
                <tbody>
                  {profiles.map((row) => (
                    <tr key={`${row.provider}:${row.model_id}`} className="border-t border-[var(--border)]">
                      <td className="py-2 font-medium">{row.display_label || formatModelLabel(row.provider, row.display_name || row.model_id)}</td>
                      <td>{row.runs}</td>
                      <td>{formatPct(row.observed_success_rate)}</td>
                      <td>{formatDuration(row.median_duration_ms)}</td>
                      <td>{formatNumber(row.average_tokens, 0)}</td>
                      <td>{formatUsd(row.average_cost_usd)}</td>
                      <td>{formatPct(row.tool_success_rate)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4">
            <h2 className="text-sm font-medium">Tool intelligence</h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="text-xs uppercase text-[var(--muted)]">
                  <tr>
                    <th className="py-2">Tool</th>
                    <th>Calls</th>
                    <th>Success</th>
                    <th>Failed</th>
                    <th>Retries</th>
                    <th>Median latency</th>
                  </tr>
                </thead>
                <tbody>
                  {tools.map((row) => (
                    <tr key={row.tool_name} className="border-t border-[var(--border)]">
                      <td className="mono py-2">{row.tool_name}</td>
                      <td>{row.calls}</td>
                      <td>{formatPct(row.success_rate)}</td>
                      <td>{row.failed}</td>
                      <td>{row.retries}</td>
                      <td>{formatDuration(row.median_latency_ms)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4">
            <h2 className="text-sm font-medium">Execution history</h2>
            <div className="mt-3 overflow-x-auto">
              <table className="w-full min-w-[860px] text-left text-sm">
                <thead className="text-xs uppercase text-[var(--muted)]">
                  <tr>
                    <th className="py-2">Time</th>
                    <th>Model</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>LLM</th>
                    <th>Tools</th>
                    <th>Tokens</th>
                    <th>Cost</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((row) => (
                    <tr
                      key={row.execution_id}
                      className="cursor-pointer border-t border-[var(--border)] hover:bg-white/5"
                      onClick={() => setParams({ execution: row.execution_id })}
                    >
                      <td className="py-2 text-xs text-[var(--muted)]">{row.started_at?.slice(11, 19)}</td>
                      <td>{row.model}</td>
                      <td>{row.task_type}</td>
                      <td>{row.outcome || row.status}</td>
                      <td>{row.llm_calls}</td>
                      <td>{row.tool_calls}</td>
                      <td>{formatNumber(row.total_tokens)}</td>
                      <td>{formatUsd(row.estimated_cost_usd)}</td>
                      <td>{formatDuration(row.duration_ms)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {detail ? (
        <section className="space-y-4 rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium">Execution detail</h2>
            <button className="text-xs text-[var(--muted)]" onClick={() => setParams({})}>
              Close
            </button>
          </div>
          <ExecutionFingerprint fingerprint={detail.fingerprint} />
          <div className="grid gap-3 md:grid-cols-3">
            <div>
              <h3 className="text-xs uppercase text-[var(--muted)]">Code impact</h3>
              <pre className="mt-2 overflow-x-auto text-xs text-[var(--muted)]">{JSON.stringify(detail.code_impact, null, 2)}</pre>
            </div>
            <div>
              <h3 className="text-xs uppercase text-[var(--muted)]">Workflow</h3>
              <pre className="mt-2 overflow-x-auto text-xs text-[var(--muted)]">{JSON.stringify(detail.workflow, null, 2)}</pre>
            </div>
            <div>
              <h3 className="text-xs uppercase text-[var(--muted)]">Context</h3>
              <pre className="mt-2 overflow-x-auto text-xs text-[var(--muted)]">{JSON.stringify(detail.context, null, 2)}</pre>
            </div>
          </div>
          <h3 className="text-xs uppercase text-[var(--muted)]">Session trajectory</h3>
          <ExecutionTrace events={detail.events} />
        </section>
      ) : null}
    </div>
  );
}
