-- AgentLens telemetry schema for Supabase Postgres
-- Run this in the SQL editor of a free Supabase project.

create extension if not exists "pgcrypto";

create table if not exists installations (
  id uuid primary key,
  created_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  metadata jsonb
);

create table if not exists workspaces (
  id text primary key,
  installation_id uuid references installations(id),
  name text not null,
  type text not null,
  created_at timestamptz not null default now(),
  metadata jsonb
);

create table if not exists comparison_groups (
  id uuid primary key,
  installation_id uuid references installations(id),
  name text not null,
  description text,
  created_at timestamptz not null default now()
);

create table if not exists tasks (
  id uuid primary key,
  installation_id uuid references installations(id),
  workspace_id text references workspaces(id),
  task_text text not null,
  task_type text not null,
  rag_enabled boolean not null default false,
  comparison_group_id uuid references comparison_groups(id),
  created_at timestamptz not null default now()
);

create table if not exists executions (
  id uuid primary key,
  task_id uuid references tasks(id),
  installation_id uuid references installations(id),
  workspace_id text,
  comparison_group_id uuid references comparison_groups(id),
  provider text not null,
  model_id text not null,
  model_version text,
  status text not null,
  started_at timestamptz not null,
  completed_at timestamptz,
  duration_ms bigint,
  llm_call_count integer default 0,
  tool_call_count integer default 0,
  retry_count integer default 0,
  files_read_count integer default 0,
  files_modified_count integer default 0,
  command_count integer default 0,
  rag_query_count integer default 0,
  chunks_retrieved integer default 0,
  tests_run integer default 0,
  tests_passed integer default 0,
  outcome text,
  final_output text,
  estimated_cost_usd numeric,
  time_to_first_edit_ms bigint,
  tool_error_count integer default 0,
  files_touched_count integer default 0,
  lines_added integer default 0,
  lines_removed integer default 0,
  edit_count integer default 0,
  correction_detected boolean default false,
  abandoned boolean default false,
  metadata jsonb
);

create table if not exists llm_events (
  id uuid primary key,
  execution_id uuid references executions(id),
  sequence_no integer not null,
  provider text not null,
  model_id text not null,
  model_version text,
  started_at timestamptz not null,
  completed_at timestamptz,
  latency_ms bigint,
  queue_time_ms bigint,
  input_tokens bigint,
  output_tokens bigint,
  total_tokens bigint,
  cached_tokens bigint,
  reasoning_tokens bigint,
  tool_tokens bigint,
  usage_available boolean not null,
  input_cost_usd numeric,
  output_cost_usd numeric,
  estimated_cost_usd numeric,
  pricing_version text,
  status text not null,
  error_type text,
  metadata jsonb
);

create table if not exists tool_events (
  id uuid primary key,
  execution_id uuid references executions(id),
  sequence_no integer not null,
  tool_name text not null,
  started_at timestamptz not null,
  completed_at timestamptz,
  latency_ms bigint,
  status text not null,
  retry_no integer default 0,
  input_metadata jsonb,
  output_metadata jsonb,
  error_type text
);

create table if not exists rag_events (
  id uuid primary key,
  execution_id uuid references executions(id),
  sequence_no integer not null,
  query_hash text,
  top_k integer not null,
  result_count integer not null,
  retrieval_latency_ms bigint,
  retrieved_chunk_count integer,
  estimated_retrieved_tokens bigint,
  context_selected_tokens bigint,
  metadata jsonb,
  created_at timestamptz not null default now()
);

create table if not exists execution_events (
  id uuid primary key,
  execution_id uuid references executions(id),
  sequence_no integer not null,
  event_type text not null,
  event_time timestamptz not null,
  summary text not null,
  metadata jsonb
);

create table if not exists edit_events (
  id uuid primary key,
  execution_id uuid references executions(id),
  sequence_no integer not null,
  file_path text not null,
  operation text not null,
  timestamp timestamptz not null,
  lines_added integer,
  lines_removed integer,
  changed_lines integer,
  content_size_before integer,
  content_size_after integer,
  is_repeat_file_edit boolean default false
);

create table if not exists model_pricing (
  id uuid primary key default gen_random_uuid(),
  provider text not null,
  model_id text not null,
  pricing_version text not null,
  input_usd_per_1m numeric,
  output_usd_per_1m numeric,
  cache_read_usd_per_1m numeric,
  cache_write_usd_per_1m numeric,
  effective_from timestamptz not null default now(),
  effective_to timestamptz,
  unique (provider, model_id, pricing_version)
);

create table if not exists model_catalog (
  id uuid primary key default gen_random_uuid(),
  provider text not null,
  model_id text not null,
  display_name text not null,
  enabled boolean not null default true,
  context_window integer,
  supports_tools boolean not null default true,
  supports_rag boolean not null default true,
  metadata jsonb
);

create index if not exists executions_installation_idx on executions (installation_id);
create index if not exists executions_model_idx on executions (model_id);
create index if not exists executions_provider_idx on executions (provider);
create index if not exists executions_group_idx on executions (comparison_group_id);
create index if not exists executions_status_idx on executions (status);
create index if not exists llm_events_execution_idx on llm_events (execution_id);
create index if not exists tool_events_execution_idx on tool_events (execution_id);
create index if not exists tool_events_name_idx on tool_events (tool_name);
create index if not exists rag_events_execution_idx on rag_events (execution_id);
create index if not exists execution_events_seq_idx on execution_events (execution_id, sequence_no);
create index if not exists edit_events_execution_idx on edit_events (execution_id);
