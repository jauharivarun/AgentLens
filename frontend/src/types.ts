export type ModelOption = {
  provider: string;
  model_id: string;
  display_name: string;
  context_window: number | null;
  supports_tools: boolean;
  supports_rag: boolean;
  configured: boolean;
};

export type ExecutionEvent = {
  id: string;
  execution_id: string;
  sequence_no: number;
  event_type: string;
  event_time: string;
  summary: string;
  metadata?: Record<string, unknown>;
};

export type Fingerprint = {
  execution_id: string;
  model: string;
  model_id?: string;
  display_name?: string;
  provider: string;
  task_type: string;
  outcome: string | null;
  llm_calls: number;
  tool_calls: number;
  files_touched: number;
  rag_calls: number;
  retries: number;
  duration_ms: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  cached_tokens: number | null;
  total_tokens: number | null;
  estimated_cost_usd: number | null;
  pricing_coverage: number | null;
  status: string;
};

export type ComparisonGroup = {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
};

export type Overview = {
  executions: number;
  llm_calls: number;
  total_tokens: number | null;
  estimated_cost_usd: number | null;
  median_duration_ms: number | null;
  tool_calls: number;
  tool_success_rate: number | null;
  pricing_coverage: number | null;
};

export type ModelProfile = {
  provider: string;
  model_id: string;
  display_name?: string;
  display_label?: string;
  runs: number;
  observed_success_rate: number | null;
  median_duration_ms: number | null;
  average_tokens: number | null;
  average_cost_usd: number | null;
  average_tool_calls: number | null;
  tool_success_rate: number | null;
  label: string;
};

export type ToolRow = {
  tool_name: string;
  calls: number;
  successful: number;
  failed: number;
  retries: number;
  success_rate: number | null;
  average_latency_ms: number | null;
  median_latency_ms: number | null;
};

export type HistoryRow = Fingerprint & {
  started_at: string;
  task_preview: string;
  task_text?: string;
  final_output?: string | null;
  comparison_group_id: string | null;
  rag_enabled?: boolean;
};

export type ExecutionDetail = {
  execution: Record<string, unknown>;
  task: Record<string, unknown>;
  fingerprint: Fingerprint;
  events: ExecutionEvent[];
  llm_events: Record<string, unknown>[];
  tool_events: Record<string, unknown>[];
  rag_events: Record<string, unknown>[];
  edit_events: Record<string, unknown>[];
  code_impact: Record<string, unknown>;
  workflow: Record<string, unknown>;
  tool_intelligence: Record<string, unknown>;
  context: Record<string, unknown>;
};
