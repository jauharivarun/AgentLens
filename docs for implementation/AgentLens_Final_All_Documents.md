# 01_PRD.md

# AgentLens — Product Requirements Document (PRD)

## 1. Document Purpose

This document defines the product requirements for **AgentLens**, a lightweight AI agent workspace with built-in LLM observability.

It is intended to be given directly to an AI coding agent such as Cursor. The implementation must follow this document unless a later instruction explicitly changes a requirement.

---

## 2. Product Definition

### App Name
**AgentLens**

### Tagline
**Build with AI. See what it costs.**

### One-line Idea
AgentLens is a general-purpose tool-using AI agent with a model selector and a second Observability page that records and analyzes model usage, token consumption, tool activity, context usage, execution behavior, latency, estimated cost, and objective task outcomes.

### Core Product Thesis

The product is not primarily a token counter and not a generic chatbot.

The core thesis is:

> AI agents are becoming capable of performing multi-step work, but developers need visibility into how that work is executed: which model was selected, which tools were called, how much context was processed, how long the run took, what it approximately cost, and whether the additional computation produced a better observable outcome.

AgentLens therefore separates:
1. **Agent execution**
2. **Telemetry collection**
3. **Observability and analytics**

---

## 3. Assignment Context

The project is being built for an open-ended AI Engineer assignment.

The assignment explicitly evaluates reasoning, product thinking, architecture, execution, prioritization, and decision-making under ambiguity. It does not prescribe a technology stack or require the project to be built inside the company's IDE.

The company product being studied is Superbrain, which has an IDE, an Agent, and a proprietary context architecture. The assignment specifically asks the candidate to understand how those components interact.

AgentLens should therefore be positioned as an adjacent exploration of **agent observability and model economics**, not as a clone of Superbrain.

---

## 4. Target Users

### Primary User
Software developers and AI engineers who use LLM-powered agents to perform work.

### Secondary User
AI/ML engineers evaluating models for agentic workloads.

### Future Users
Engineering managers and technical leads who need aggregate AI usage/cost visibility.

---

## 5. User Problem

Current AI-agent interfaces generally tell users what the agent answered or changed, but they often make it difficult to understand the complete execution profile.

A user may want to know:

- Which model did I run?
- How many LLM calls occurred?
- How many tool calls occurred?
- Which tools were used?
- Which tools failed or were retried?
- How much input/output/context was processed?
- How much of the context was retrieved versus actually sent?
- How long did the execution take?
- What is the estimated provider cost?
- Did the task actually succeed?
- Did the model require more computation than another model for the same task?
- Was additional token usage associated with a better observable result?

AgentLens addresses these questions without requiring the user to put model information into the task prompt.

---

## 6. Product Principles

1. **Model selection is UI state, not prompt content.**
2. **Telemetry is collected automatically.**
3. **Observed metrics should be provider/API-derived or runtime-derived whenever possible.**
4. **Avoid subjective LLM-generated performance scores in the MVP.**
5. **Do not compare raw tokens across unrelated tasks without workload context.**
6. **The same task can be manually repeated with different model selections and grouped for comparison.**
7. **The agent should be genuinely tool-using, not a chat wrapper.**
8. **The first version prioritizes reliable execution and observability over feature breadth.**
9. **API keys remain server-side and are never exposed to the browser.**
10. **The architecture must allow additional model providers later.**

---

## 7. Core User Experience

The application has one shell/window with two primary pages:

### Page 1 — Agent
The user:
- selects a model from a dropdown;
- enters a task;
- optionally selects a workspace/repository;
- optionally uses RAG;
- runs the agent;
- watches the execution trace;
- receives the final result.

### Page 2 — Observability
The user:
- sees aggregated usage;
- filters by model, task, time range, task type, and comparison group;
- inspects individual executions;
- sees tool usage;
- sees token/context metrics;
- sees latency and estimated cost;
- compares repeated runs of the same task manually;
- inspects execution traces.

---

## 8. Model Selection

The Agent page must contain a model dropdown similar in concept to a modern AI coding tool.

Example:

- Provider A / Model A
- Provider A / Model B
- Provider B / Model C

The exact currently enabled models are configuration-driven and must not be hard-coded into prompts.

The selected model is stored in the execution metadata.

The user's task prompt must not be modified with text such as:
> "Use GPT-OSS 120B"

The model is selected outside the prompt.

---

## 9. Agent Capabilities — MVP

The agent must support:

### Reasoning
- multi-step task planning;
- iterative LLM calls;
- structured tool calls.

### Workspace tools
- list files;
- read file;
- search files;
- create/update file;
- run a safe command where supported.

### RAG
- ingest sample documents;
- chunk documents;
- embed/index documents in hosted Chroma;
- retrieve relevant chunks;
- provide retrieved context to the LLM;
- expose retrieval events in telemetry.

### Execution
- multiple LLM calls per task;
- tool calls between LLM calls;
- retries on recoverable failures;
- final response.

---

## 10. Observability Requirements

Every LLM invocation should produce a telemetry event containing, where available:

### Model metrics
- provider;
- model ID;
- model version/system fingerprint if returned;
- input/prompt tokens;
- output/completion tokens;
- total tokens;
- cached tokens;
- reasoning/thinking tokens if provider exposes them.

### Timing metrics
- request start;
- request end;
- total latency;
- provider queue time if available;
- provider inference time if available.

### Runtime metrics
- task ID;
- execution ID;
- LLM call number;
- tool calls before/after;
- retry count;
- failure status;
- task type.

### Cost metrics
- provider;
- model;
- pricing version;
- input price;
- output price;
- estimated input cost;
- estimated output cost;
- estimated total cost.

Cost is always labeled **estimated**.

---

## 11. Tool Observability

Every tool call must produce a tool event.

Minimum fields:

- tool name;
- sequence number;
- start time;
- end time;
- latency;
- status;
- error type if failed;
- retry number;
- high-level input metadata;
- output metadata;
- execution ID.

Do not store sensitive raw tool output unnecessarily.

The dashboard must be able to answer:
- Which tools were used?
- How often?
- How successful were they?
- How much time did they consume?
- How many retries occurred?

---

## 12. Context and RAG Observability

For RAG runs, record:

- retrieval query count;
- documents/chunks retrieved;
- retrieval latency;
- embedding/indexing status;
- retrieved token estimate if available;
- context selected;
- context sent to model;
- cached context if provider reports it.

Do not claim that retrieved context is "correct" simply because the LLM used it.

---

## 13. Workload-Aware Analytics

Raw tokens per task are not sufficient.

AgentLens should show workload descriptors:

- LLM calls;
- tool calls;
- files read;
- files modified;
- commands executed;
- tests executed;
- RAG searches;
- chunks retrieved;
- retries;
- task duration.

Derived metrics can include:

### Tool success rate
successful tool calls / total tool calls

### Cost per successful execution
estimated cost / objectively successful execution

### Tokens per tool action
total tokens / successful tool actions

### LLM calls per execution
LLM calls / execution

### Tool calls per execution
tool calls / execution

### Context utilization
model input context / available selected context, where measurable

These are descriptive metrics, not universal measures of model quality.

---

## 14. Manual Same-Task Model Comparison

AgentLens must support a **Comparison Group** field.

The user can:

1. Create a comparison group.
2. Run the same task manually.
3. Select Model A from the dropdown.
4. Run the task.
5. Select Model B.
6. Run the same task.
7. Open Observability.
8. Filter to the comparison group.
9. Compare the executions side by side.

The task prompt itself remains model-agnostic.

The comparison page must not assume that one model is "better."

It should show observed differences in:
- success/outcome status;
- latency;
- LLM calls;
- tool calls;
- retries;
- input tokens;
- output tokens;
- cached tokens;
- total tokens;
- estimated cost;
- tool success rate;
- RAG retrieval metrics;
- files changed;
- tests passed where applicable.

---

## 15. Innovative Feature: Execution Fingerprint

Each completed execution should have a compact "Execution Fingerprint":

- model;
- task type;
- LLM calls;
- tool calls;
- files touched;
- RAG calls;
- retries;
- duration;
- token usage;
- estimated cost;
- outcome.

This gives the user a fast way to compare how two agents behaved without reducing the analysis to token count.

---

## 16. Innovative Feature: Model Efficiency Profile

The Observability page should optionally show a descriptive profile for each model based only on the user's observed runs:

- median latency;
- average input tokens;
- average output tokens;
- average tool calls;
- tool success rate;
- average estimated cost;
- observed success rate;
- cost per successful run.

The UI must clearly state:
> "Based on your observed runs."

Do not present the result as a universal benchmark.

---

## 17. Task Types

The MVP should support at least:

1. General Q&A
2. Coding/file modification
3. RAG question answering
4. Document summarization
5. Data/file analysis
6. Tool-driven task

The user can optionally select a task type. If not selected, the system can classify it as "General".

---

## 18. Example Use Cases

### Use Case A — Coding Task
User:
> Create a Python utility that reads a CSV and produces a summary report.

Agent:
- inspect workspace;
- create file;
- run command/test;
- report result.

Observability:
- model;
- LLM calls;
- tool calls;
- files touched;
- command runs;
- tokens;
- latency;
- cost;
- outcome.

### Use Case B — RAG
User:
> What are the main requirements in the uploaded sustainability documents?

Agent:
- search vector store;
- retrieve chunks;
- answer with references.

Observability additionally shows:
- retrieval count;
- chunks;
- retrieval latency;
- context metrics.

### Use Case C — Same Task, Different Models
User runs the same coding task twice, manually selecting different models.

Observability comparison shows:
- Model A and Model B side by side;
- no model name injected into the prompt;
- objective execution differences.

### Use Case D — Failed Tool
Agent calls `run_command`, command fails, agent retries.

Observability:
- failed tool event;
- retry;
- final success/failure;
- additional latency/tokens.

### Use Case E — Expensive Context
Agent retrieves a large number of chunks.

Observability:
- retrieved chunks;
- input token growth;
- context utilization;
- cost impact.

---

## 19. MVP Scope

### Must Have
- React/Vite frontend;
- FastAPI backend;
- model selector;
- one or more configured LLM providers;
- general tool-using agent;
- workspace/file tools;
- RAG capability;
- hosted Chroma;
- LLM gateway;
- telemetry;
- token usage capture;
- tool trace;
- execution trace;
- estimated cost;
- Observability page;
- filters;
- comparison groups;
- side-by-side comparison;
- persisted telemetry;
- Vercel deployment;
- sample/demo data or sample workspace.

### Should Have
- second provider;
- context efficiency metrics;
- model efficiency profile;
- export execution JSON/CSV;
- trace detail view.

### Not in V1
- authentication;
- billing;
- team management;
- full IDE fork;
- GitHub OAuth;
- autonomous PR creation;
- multi-agent orchestration;
- automatic model routing;
- automatic model ranking;
- fine-tuning;
- enterprise observability;
- complex long-term memory.

---

## 20. Success Metrics

The MVP is successful if:

1. A user can select a model and run a real agent task.
2. The agent can call tools and complete a multi-step task.
3. At least one RAG workflow works.
4. Each LLM call records provider usage data when the provider returns it.
5. Each tool call is recorded.
6. Observability updates after an execution.
7. Two manually repeated runs can be grouped and compared.
8. No model name is inserted into the user's task prompt.
9. API keys never reach the frontend.
10. The application works locally.
11. The application is deployed on Vercel.
12. A fresh evaluator can understand the product without explanation.

---

## 21. Product Success Beyond the Assignment

If extended, AgentLens could evolve into:
- persistent engineering AI telemetry;
- model selection recommendations based on actual workloads;
- context optimization;
- cost budgets;
- team-level analytics;
- provider comparison;
- agent regression testing;
- evaluation datasets;
- model routing;
- OpenTelemetry-compatible traces.

These are future directions, not MVP commitments.

AgentLens will adopt the following ideas while keeping its own architecture and scope:

- **Code impact:** lines added/removed, files touched, edits per execution, output tokens per edit, cost per edit, and cost per 100 changed lines.
- **Workflow signals:** rework loops, cross-run file churn, explicit correction follow-ups, abandoned executions, and time to first edit.
- **Tool intelligence:** tool error rate and median tool latency.
- **Cache efficiency:** cache-read tokens / input tokens when provider data is available.
- **Pricing coverage:** show the percentage of usage for which pricing is known; never silently guess unknown model pricing.
- **Session trajectory:** every execution can be inspected as a chronological event stream.
- **Execution fingerprint:** summarize model + work performed + outcome rather than only tokens.

## Final Feature Scope

The six core documents define the original AgentLens MVP. Only adopted features are included in these documents. Optional future enhancements are maintained separately in `07_RECOMMENDATIONS_FOR_FUTURE.md`.


---

# 02_TRD.md

# AgentLens — Technical Requirements Document (TRD)

## 1. Technical Objective

Build a lightweight, modular AI agent and LLM observability system that can run locally and deploy on Vercel without paid infrastructure.

The architecture must prioritize:
- fast implementation;
- clear separation of concerns;
- provider independence;
- secure API key handling;
- complete execution telemetry;
- hosted vector storage;
- objective analytics.

---

## 2. Required Stack

### Frontend
- React
- Vite
- TypeScript
- Recharts or equivalent chart library
- Tailwind CSS or a similarly fast utility/component approach

### Backend
- Python
- FastAPI
- Pydantic
- Async HTTP client where appropriate

### Agent
- Python
- Provider SDKs or OpenAI-compatible clients
- Custom lightweight agent loop
- Do not introduce LangChain unless a concrete requirement justifies it

### Vector Database
**Chroma Cloud**

Reason:
- hosted/serverless;
- same Chroma concepts already known by the developer;
- avoids local persistence;
- free credits are currently available;
- suitable for a small RAG assignment workload.

### Persistent Application Database
**Supabase Postgres Free Plan**

Use this only for:
- execution metadata;
- telemetry events;
- comparison groups;
- model configuration metadata if needed.

Do not store large document bodies or embeddings in Postgres.

Supabase Free currently includes a Postgres database with a 500 MB database quota; free projects may pause after inactivity. This is acceptable for an assignment/demo environment.

### Deployment
Vercel.

FastAPI is supported directly by Vercel's Python runtime and can be deployed as a Vercel Function.

---

## 3. High-Level Architecture

```text
Browser
  |
  | HTTPS
  v
React/Vite
  |
  | REST / streaming
  v
FastAPI
  |
  +-----------------------+
  |                       |
  v                       v
Agent Runtime          Observability API
  |
  +-------------+-------------+-------------+
  |             |             |             |
  v             v             v             v
LLM Gateway   Workspace     RAG Service   Telemetry
              Tools                       Engine
  |                           |
  +-------------+-------------+
                |
        +-------+-------+
        |               |
        v               v
   LLM Providers   Chroma Cloud
        |
        v
 Provider response + usage metadata

Telemetry
   |
   v
Supabase Postgres
   |
   v
Analytics queries
   |
   v
Observability UI
```

---

## 4. Core Architectural Rule

All model calls must pass through `LLM Gateway`.

Do not allow agent tools or route handlers to call provider APIs directly.

### Required abstraction

```python
class LLMGateway:
    async def generate(
        self,
        *,
        provider: str,
        model: str,
        messages: list,
        tools: list | None,
        task_id: str,
        execution_id: str,
    ) -> LLMResult:
        ...
```

The gateway:
1. validates provider/model;
2. starts telemetry timing;
3. sends request;
4. receives provider response;
5. extracts usage;
6. normalizes usage;
7. calculates estimated cost;
8. records telemetry;
9. returns normalized response to the agent.

---

## 5. Provider Abstraction

Create a provider adapter interface:

```python
class ProviderAdapter(Protocol):
    async def generate(...): ...
    def normalize_usage(...): ...
    def get_model_catalog(...): ...
```

Initial providers:

### Provider 1
Groq.

Use a small set of currently available models configured through environment/config.

### Provider 2
Gemini.

Implement only if time allows after the first provider is stable.

The UI must be provider/model agnostic.

---

## 6. Token Usage Acquisition

Do not query a provider billing dashboard.

Capture usage directly from each API response.

### Groq
Normalize fields such as:
- prompt_tokens;
- completion_tokens;
- total_tokens;
- cached_tokens when available;
- queue_time;
- prompt_time;
- completion_time;
- total_time.

Groq's API returns usage statistics in the completion response.

### Gemini
Normalize fields such as:
- prompt_token_count;
- candidates_token_count;
- total_token_count;
- cached_content_token_count where available;
- thoughts_token_count where available;
- tool-use prompt token counts where available.

The provider adapter must tolerate missing fields.

### Normalized Usage Object

```json
{
  "input_tokens": 0,
  "output_tokens": 0,
  "total_tokens": 0,
  "cached_tokens": 0,
  "reasoning_tokens": 0,
  "tool_tokens": 0,
  "usage_available": true
}
```

Unknown values must be `null`, not guessed.

---

## 7. Cost Calculation

Cost must be calculated from a versioned pricing configuration.

Example:

```json
{
  "provider": "groq",
  "model": "MODEL_ID",
  "pricing_version": "YYYY-MM-DD",
  "input_usd_per_1m": 0.0,
  "output_usd_per_1m": 0.0
}
```

Formula:

```text
input_cost = input_tokens / 1,000,000 * input_price
output_cost = output_tokens / 1,000,000 * output_price
estimated_cost = input_cost + output_cost
```

If a provider/model does not have configured pricing:
- display token usage;
- display cost as "N/A";
- never invent a price.

---

## 8. Agent Runtime

The MVP agent is a single agent with iterative tool use.

Loop:

```text
receive task
  |
  v
create execution
  |
  v
LLM call
  |
  +--> final answer -> finish
  |
  +--> tool call
          |
          v
      execute tool
          |
          v
      record tool event
          |
          v
      append tool result
          |
          v
       next LLM call
```

Maximum configurable iteration count:
- default: 12;
- hard limit configurable.

This prevents infinite loops.

---

## 9. Tool Set

### `list_files`
Input:
- workspace path

Output:
- file paths only.

### `read_file`
Input:
- relative path
- optional line range

Output:
- bounded file content.

### `search_files`
Input:
- query
- optional path

Output:
- matching file paths/line snippets.

### `write_file`
Input:
- relative path
- content

Output:
- status.

### `run_command`
Input:
- allowlisted command.

For MVP, do not expose arbitrary shell execution on a public deployment.

Use a controlled demo workspace and an allowlist such as:
- Python test commands;
- package-independent safe commands.

### `rag_search`
Input:
- query
- top_k

Output:
- document IDs;
- chunk IDs;
- similarity metadata;
- chunk text.

---

## 10. Workspace Security

Because Vercel/serverless deployment is not a persistent shell environment, the MVP must distinguish:

### Local development
A local demo workspace can be used.

### Public deployment
Do not expose arbitrary host filesystem access or unrestricted shell commands.

The deployed version should use a controlled sample workspace or sandbox-safe operations.

Never allow:
- `rm -rf`;
- arbitrary network commands;
- environment variable reads;
- process spawning without restrictions;
- access outside the designated workspace.

---

## 11. RAG Architecture

```text
Documents
  |
  v
Parser
  |
  v
Chunker
  |
  v
Embedding
  |
  v
Chroma Cloud
  |
  v
Retriever
  |
  v
Top-K chunks
  |
  v
Context builder
  |
  v
LLM Gateway
```

### Ingestion
For MVP:
- TXT;
- Markdown;
- PDF where practical.

PDF extraction should be kept simple.

### Chunk metadata
Each chunk should store:
- document_id;
- filename;
- page/section if available;
- chunk_index;
- source reference.

### Retrieval telemetry
Record:
- query;
- top_k;
- result count;
- retrieval latency;
- document/chunk IDs;
- estimated retrieved characters/tokens.

Do not store unnecessary sensitive document text in telemetry.

---

## 12. Database Choice

Use Supabase Postgres for persistent execution telemetry.

Reason:
- free tier;
- managed;
- PostgreSQL;
- suitable for relational execution data;
- works with serverless applications;
- avoids maintaining a server.

Use Chroma Cloud only for vector retrieval.

Do not mix telemetry tables into Chroma.

---

## 13. API Endpoints

### Health
`GET /api/health`

### Models
`GET /api/models`

Returns enabled provider/model configurations safe for the frontend.

Never return API keys.

### Start execution
`POST /api/executions`

Request:
```json
{
  "task": "Create a CSV summary utility",
  "model": {
    "provider": "groq",
    "model_id": "MODEL_ID"
  },
  "task_type": "coding",
  "comparison_group_id": null,
  "workspace_id": "demo-workspace",
  "rag_enabled": false
}
```

Response:
```json
{
  "execution_id": "uuid",
  "status": "started"
}
```

### Execution events
`GET /api/executions/{execution_id}/events`

### Execution result
`GET /api/executions/{execution_id}`

### Observability summary
`GET /api/analytics/overview`

Query filters:
- date range;
- provider;
- model;
- task type;
- comparison group.

### Model analytics
`GET /api/analytics/models`

### Tool analytics
`GET /api/analytics/tools`

### Comparison
`GET /api/analytics/comparisons/{comparison_group_id}`

### Comparison group creation
`POST /api/comparison-groups`

### RAG ingestion
`POST /api/rag/ingest`

### RAG search
Internal agent tool only:
`POST /api/rag/search`

---

## 14. Streaming

Preferred:
- Server-Sent Events (SSE) for execution events.

The frontend should receive:
- agent message;
- tool started;
- tool completed;
- LLM started;
- LLM completed;
- execution status.

Persist events separately.

If streaming causes deadline risk, implement polling first and SSE as a stretch feature.

---

## 15. Environment Variables

Backend only:

```text
GROQ_API_KEY=
GEMINI_API_KEY=

CHROMA_API_KEY=
CHROMA_TENANT=
CHROMA_DATABASE=

SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

Frontend should only receive public configuration.

Never expose:
- provider API keys;
- Supabase service role key;
- Chroma server credentials.

---

## 16. Security

MVP:
- no authentication;
- anonymous demo workspace;
- server-side secrets;
- strict CORS;
- input size limits;
- command allowlist;
- tool iteration limits;
- request timeout;
- output size limits;
- no raw API key logging.

For future:
- Supabase Auth;
- Row Level Security;
- per-user ownership;
- project/workspace permissions.

---

## 17. Performance Requirements

MVP targets:
- UI initial load under 3 seconds on a normal connection;
- telemetry event persisted without blocking the main agent loop unnecessarily;
- analytics overview query under 1 second for assignment-scale data;
- tool trace visible within a few seconds of events;
- avoid loading all historical events into the browser at once.

---

## 18. Reliability

If an LLM call fails:
1. record failure event;
2. classify error;
3. retry only when safe;
4. increment retry count;
5. stop after configured maximum;
6. surface clear status to user.

If telemetry persistence fails:
- do not destroy the agent result;
- log the telemetry failure;
- mark the event as unsynced if an event queue is implemented.

---

## 19. Deployment Architecture

Vercel:
- React frontend;
- FastAPI backend;
- environment variables;
- serverless runtime.

Supabase:
- telemetry persistence.

Chroma Cloud:
- vector storage/retrieval.

LLM provider:
- Groq initially;
- Gemini optional.

No AWS server is required for MVP.

---

## 20. Technical Constraints

Do not:
- add a second backend framework;
- introduce Kubernetes;
- introduce Redis;
- introduce Kafka;
- introduce a full observability platform;
- introduce microservices;
- introduce a multi-agent framework;
- add authentication before the core workflow works.

The system should remain small enough to complete and test within the assignment deadline.

---

## 21. Reference Architecture Decision

The main engineering decision is:

> **Instrument the agent at the LLM Gateway and Tool Runtime boundaries.**

This creates a provider-independent telemetry layer.

The agent does not know how analytics are calculated.

The dashboard does not need to know how the agent thinks.

The telemetry layer connects the two.

### Normalized event model
Every runtime event must contain:
- `event_id`
- `execution_id`
- `sequence_no`
- `timestamp`
- `event_type`
- `metadata`

Supported event types include:
`execution_started`, `user_message`, `llm_started`, `llm_completed`, `tool_started`, `tool_completed`, `file_edit`, `rag_started`, `rag_completed`, `retry`, `correction`, `execution_abandoned`, `execution_completed`, `execution_failed`.

### Code-impact calculations
Because AgentLens controls its file-edit tools, it can measure old/new file content and calculate additions/removals directly. Where an exact diff cannot be calculated, the UI must mark the value as approximate rather than inventing precision.

### Pricing

### Workflow heuristics

### Future adapter architecture

## Final Feature Scope

The six core documents define the original AgentLens MVP. Only adopted features are included in these documents. Optional future enhancements are maintained separately in `07_RECOMMENDATIONS_FOR_FUTURE.md`.


---

# 03_APP_FLOW.md

# AgentLens — App Flow Document

## 1. Application Shell

The application has one main shell.

```text
AgentLens
------------------------------------------------
[ Agent ] [ Observability ]       Model: ______
------------------------------------------------
Current page
```

Primary navigation:
- Agent
- Observability

No login page in MVP.

---

## 2. First Load

### User sees
- AgentLens branding;
- Agent page;
- model dropdown;
- task input;
- workspace selector;
- optional RAG toggle;
- optional task type;
- optional comparison group;
- Run button.

### Empty state
Show:
> "Give the agent a task to start an execution."

Provide example tasks:
- "Create a Python CSV summary utility."
- "Search the knowledge base and summarize the procurement policy."
- "Inspect the sample project and explain how the API works."

---

## 3. Model Selection Flow

1. User opens model dropdown.
2. Frontend calls `GET /api/models`.
3. Enabled models are shown.
4. User selects a model.
5. Selected model becomes execution metadata.
6. Do not modify the user's task prompt.
7. Run task.

### Important
The user prompt must remain exactly as entered, except for normal system/context assembly performed by the agent runtime.

---

## 4. Create Comparison Group

The user can click:
> "New comparison group"

Dialog:
- Name
- Optional description

Example:
> "RAG policy summary — model comparison"

After creation:
- group appears in Agent page;
- user can select it for subsequent executions.

---

## 5. Agent Task Flow

```text
User enters task
      |
      v
Select model
      |
      v
Optional task type
      |
      v
Optional RAG
      |
      v
Optional comparison group
      |
      v
Run
      |
      v
Create execution
      |
      v
Agent begins
```

---

## 6. Execution View

While running, show a live trace.

Example:

```text
03:21:02  Execution started

03:21:02  LLM call started

03:21:03  Tool: list_files

03:21:04  Tool completed

03:21:05  LLM call completed
          2,143 input / 412 output tokens

03:21:06  Tool: read_file

03:21:08  Tool completed

03:21:09  LLM call started

03:21:12  Final response generated
```

The user should be able to expand an event.

---

## 7. Tool Event Expansion

For each tool:
- name;
- status;
- duration;
- sequence;
- high-level input;
- output metadata;
- error if any.

Do not expose secrets.

Do not expose full internal prompts.

---

## 8. LLM Event Expansion

Show:
- provider;
- model;
- call number;
- input tokens;
- output tokens;
- total tokens;
- cached tokens if available;
- reasoning tokens if available;
- latency;
- estimated cost.

The model name can appear in telemetry/UI.

It should not be injected into the task prompt.

---

## 9. RAG Flow

### User
Turns on:
> RAG

Selects:
> Knowledge Base

Enters:
> "What are the main procurement requirements?"

### Agent
1. calls `rag_search`;
2. receives top chunks;
3. builds context;
4. calls selected model;
5. returns answer with source references.

### UI
Show:
- retrieval event;
- number of chunks;
- documents;
- retrieval latency;
- final answer;
- sources.

---

## 10. File/Coding Flow

Example:
> "Create a Python script that summarizes sales.csv."

Agent:
1. list files;
2. read CSV;
3. create script;
4. run test/command;
5. inspect result;
6. fix if needed;
7. return summary.

Observability captures:
- files read;
- files changed;
- tool calls;
- command executions;
- retries;
- test results;
- model usage.

---

## 11. Failure Flow

If a tool fails:

```text
Tool started
   |
   v
Tool failed
   |
   v
Record failure
   |
   v
Agent decides whether retry is appropriate
   |
   +--> retry
   |
   +--> stop and report
```

The UI must clearly distinguish:
- failed;
- retried;
- successful after retry;
- terminal failure.

---

## 12. Successful Completion

Show:
- final answer;
- execution status;
- duration;
- compact execution fingerprint.

Example:

```text
Completed

18.4s
6 LLM calls
11 tool calls
3 files touched
18.2K input tokens
4.1K output tokens
Estimated cost: $0.00XX
```

Button:
> View in Observability

---

## 13. Observability Page

Top-level sections:

### Overview
- total executions;
- total LLM calls;
- total tokens;
- estimated cost;
- average/median duration.

### Models
- executions by model;
- token distribution;
- cost;
- latency;
- success rate.

### Tools
- tool calls;
- success rate;
- retries;
- latency.

### Tasks
- execution history;
- filters;
- task type;
- outcome.

### Comparisons
- comparison groups;
- side-by-side execution table.

---

## 14. Observability Filters

Filters:
- date range;
- provider;
- model;
- task type;
- outcome;
- comparison group;
- RAG enabled;
- has tool calls;
- has retries.

Filters should update charts and tables together.

---

## 15. Execution Detail Flow

User clicks an execution.

Show:

### Summary
- task ID;
- execution ID;
- model;
- status;
- duration;
- estimated cost.

### Usage
- input tokens;
- output tokens;
- total;
- cached;
- reasoning.

### Agent behavior
- LLM calls;
- tool calls;
- retries;
- files;
- commands.

### RAG
- searches;
- chunks;
- retrieval latency;
- context metrics.

### Trace
Chronological execution timeline.

---

## 16. Manual Model Comparison Flow

This is intentionally manual.

### User process

1. Create comparison group.
2. Enter the task.
3. Select Model A.
4. Run.
5. Keep task conditions the same.
6. Select Model B.
7. Run the same task again.
8. Open Observability.
9. Select comparison group.
10. Compare.

AgentLens does not automatically alter the prompt to mention models.

---

## 17. Comparison Screen

Show rows:

| Metric | Run A | Run B |
|---|---:|---:|
| Model | | |
| Outcome | | |
| Duration | | |
| LLM calls | | |
| Tool calls | | |
| Retries | | |
| Input tokens | | |
| Output tokens | | |
| Cached tokens | | |
| Total tokens | | |
| Estimated cost | | |
| Tool success rate | | |
| Files touched | | |
| Tests passed | | |
| RAG searches | | |
| Chunks retrieved | | |

No automatic "winner" should be declared.

Instead show:
> "Observed differences"

---

## 18. Execution Fingerprint Flow

Every execution has a compact card.

Example:

```text
GPT-OSS 120B
Coding
SUCCESS

6 LLM calls
11 tools
3 files changed
18.2K input
4.1K output
18.4s
$0.00XX
```

The card can be compared with another fingerprint.

---

## 19. Empty States

### No executions
> "Run your first task to populate observability."

### No model filter results
> "No executions match the current filters."

### No comparison groups
> "Create a comparison group to compare repeated runs."

### No RAG data
> "Run a task with RAG enabled to see retrieval analytics."

---

## 20. Error States

### Provider unavailable
> "The selected model provider could not complete the request."

Show:
- provider;
- error class;
- retry option.

### Invalid model
> "This model is not currently configured."

### RAG unavailable
> "The knowledge base could not be reached."

### Telemetry unavailable
> "The task completed, but some observability data could not be persisted."

Do not hide successful task results because analytics persistence failed.

---

## 21. Navigation

Agent:
- default landing page.

Observability:
- accessible at all times.

From execution completion:
- "View in Observability".

From Observability execution:
- "Open execution in Agent" if practical.

---

## 22. V1 Navigation Must Stay Small

Do not create:
- separate billing page;
- settings dashboard;
- user management;
- integrations marketplace;
- project management;
- authentication pages.

The two-page concept is intentional.

The Observability page must not stop at token charts. Add these sections to the execution and analytics journey:

1. **Code Impact** — files touched, edits, additions, removals, output tokens/edit, cost/edit.
2. **Workflow Signals** — rework, churn, corrections, abandonment, first-edit time.
3. **Tool Intelligence** — tool error rate, median tool latency, retry count.
4. **Pricing Coverage** — known-priced versus unknown-priced model usage.
5. **Session Trajectory** — full chronological event trace.

For a coding execution, clicking an execution should let the user move from:
`Cost → Code Impact → Workflow Signal → Exact Event Trace`.

### Same-task comparison

## Final Feature Scope

The six core documents define the original AgentLens MVP. Only adopted features are included in these documents. Optional future enhancements are maintained separately in `07_RECOMMENDATIONS_FOR_FUTURE.md`.


---

# 04_UI_UX_DESIGN_BRIEF.md

# AgentLens — UI/UX Design Brief

## 1. Design Goal

AgentLens should feel like a serious developer tool rather than a generic AI chatbot.

The visual language should communicate:
- engineering;
- observability;
- clarity;
- dense but readable information;
- trust;
- system state.

The interface should be inspired by modern developer tools without copying a specific product.

---

## 2. Overall Experience

Primary shell:

```text
┌──────────────────────────────────────────────────────────────┐
│ AgentLens                         Agent  Observability       │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│                    Current Page                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

Desktop-first because the assignment is primarily an engineering/developer product.

Responsive behavior is required but mobile is secondary.

---

## 3. Visual Style

### Style
- dark developer-tool interface;
- restrained accent color;
- high information density;
- thin borders;
- subtle shadows;
- rounded but not overly playful cards;
- monospace typography for technical values;
- readable sans-serif for general UI.

Avoid:
- excessive gradients;
- oversized illustrations;
- glassmorphism everywhere;
- cartoon AI imagery;
- excessive animation.

---

## 4. Color Direction

Use semantic colors:

### Background
Very dark neutral.

### Panels
Slightly lighter dark neutral.

### Primary accent
Cool blue/violet or similar technical accent.

### Success
Green.

### Warning
Amber.

### Error
Red.

### Neutral
Muted gray.

The exact palette can be implemented through CSS variables so it is easy to adjust.

---

## 5. Typography

Recommended:
- Inter or system sans-serif for UI;
- JetBrains Mono or system monospace for:
  - tokens;
  - model IDs;
  - tool names;
  - execution IDs;
  - code.

Hierarchy:
- page title;
- section title;
- metric number;
- metric label;
- supporting text.

---

## 6. Agent Page Layout

Three conceptual regions:

```text
┌───────────────┬───────────────────────────────────────┐
│ Workspace     │ Agent conversation                    │
│ / Tasks       │                                       │
│               │                                       │
│ Demo Repo     │ User task                             │
│ Files         │ Agent response                        │
│ History       │                                       │
│               │ Tool trace                            │
│               │                                       │
├───────────────┴───────────────────────────────────────┤
│ Model ▼ | Task type ▼ | RAG ○ | Comparison ▼ | Send │
└───────────────────────────────────────────────────────┘
```

For the MVP, the left sidebar can be compact.

---

## 7. Model Selector

Model selector should be prominent but not dominant.

Example:

```text
Model
[ Groq / GPT-OSS 120B ▼ ]
```

The dropdown should display:
- provider;
- friendly model name;
- optional context window.

Do not display provider API keys.

Do not add model name to the user prompt.

---

## 8. Task Composer

Controls:
- task textarea;
- model selector;
- task type;
- RAG toggle;
- knowledge base selector;
- comparison group selector;
- Run button.

The task composer should make it obvious that the selected model is external configuration.

---

## 9. Execution Trace

Use a vertical timeline.

Example:

```text
● LLM call
│  GPT-OSS 120B
│  2,143 in / 412 out
│
● Tool
│  read_file
│  83ms
│
● Tool
│  run_command
│  SUCCESS
│
● LLM call
│  1,812 in / 608 out
```

Events should be collapsible.

---

## 10. Agent Message Design

User messages:
- right aligned or clearly separated.

Agent messages:
- left aligned.

Tool events:
- visually distinct from conversational messages.

Do not make tool calls look like normal assistant prose.

---

## 11. Observability Page

The Observability page is the most visually important part of the product.

Top:

```text
OBSERVABILITY

[24 executions] [137K tokens] [$0.XX estimated] [82 LLM calls]
```

Below:
- token trend;
- cost trend;
- model comparison;
- tool distribution;
- execution table.

---

## 12. Metric Cards

Every metric card must have:
- value;
- label;
- optional small comparison/change indicator;
- tooltip explaining the metric.

Example:

```text
137.4K
Total tokens

82
LLM calls

$0.041
Estimated cost

18.2s
Median duration
```

Avoid fake percentage changes unless based on real historical data.

---

## 13. Model Analytics

Chart types:
- bar chart for tokens by model;
- bar chart for estimated cost by model;
- scatter plot for cost vs duration if easy;
- table for observed model profile.

Model profile:

```text
Model              Runs  Success  Median Time  Avg Cost
GPT-OSS 20B         8      7/8       12.4s       $...
GPT-OSS 120B        6      6/6       17.1s       $...
```

Do not call one model "best."

---

## 14. Tool Analytics

Display:
- total tool calls;
- successful calls;
- failed calls;
- retries;
- average latency.

Chart:
- horizontal bar chart.

Example:

```text
read_file       █████████████  34
search_files    ████████       21
write_file      █████          13
run_command     ████           10
rag_search      ███             8
```

---

## 15. Execution Fingerprint Card

Use a compact card with:

```text
MODEL
TASK TYPE
OUTCOME

LLM CALLS
TOOLS
FILES
RAG
RETRIES

INPUT
OUTPUT
TOTAL TOKENS

DURATION
EST. COST
```

The user can click the card for full trace.

---

## 16. Comparison UI

Comparison screen should use a clean table.

Header:
- Run A
- Run B

Rows:
- Model;
- outcome;
- duration;
- LLM calls;
- tool calls;
- retries;
- input tokens;
- output tokens;
- cached tokens;
- total tokens;
- estimated cost;
- tool success rate;
- files touched;
- tests;
- RAG metrics.

Use subtle visual highlighting only for numerical differences, not to declare a winner.

---

## 17. Task Normalization UX

The UI should explain:

> "Raw token counts are not directly comparable across different workloads. Compare executions with the same task and conditions using a comparison group."

This is an important product education element.

---

## 18. Context Efficiency UI

Where RAG/context data exists:

```text
Context

Available selected context      24.8K
Sent to model                   14.1K
Cached                          6.2K

Utilization                     56.9%
```

Use a compact stacked bar.

If a value is unavailable, display:
> N/A

Never fabricate it.

---

## 19. Model Efficiency Profile

Display:

> Based on 12 observed runs

Then:
- median latency;
- average cost;
- average tokens;
- tool success rate;
- observed success rate.

This wording prevents the dashboard from implying universal benchmarking.

---

## 20. Interaction Principles

1. Every metric should be explainable.
2. Every execution should be inspectable.
3. Every error should be visible.
4. Avoid hidden state.
5. Do not hide provider/model information on the Observability page.
6. Do not overload the Agent page with analytics.
7. Do not overload the Observability page with chat.
8. Keep the two-page mental model extremely clear.

---

## 21. Accessibility

- keyboard-accessible controls;
- visible focus states;
- sufficient contrast;
- chart data also available in tables;
- tooltips should not be the only source of information.

---

## 22. Responsiveness

Desktop:
- full dashboard.

Tablet:
- two-column or stacked dashboard.

Mobile:
- stacked metric cards;
- horizontally scrollable comparison tables;
- collapsible navigation.

Do not compromise the desktop developer experience for mobile.

---

## 23. Loading States

Agent:
- streaming/loading indicator;
- tool event skeleton;
- model call status.

Observability:
- skeleton cards;
- chart loading state;
- table loading state.

---

## 24. Empty State Design

Empty states should be instructional.

Example:

> No executions yet.
>
> Run a task from Agent to start collecting observability data.

Button:
> Go to Agent

---

## 25. Error State Design

Errors must identify:
- what failed;
- whether the agent task also failed;
- whether telemetry was affected;
- whether retry is possible.

Example:

> Model request failed.
> Your task was not completed.
> Retry with the selected model.

---

## 26. Avoid Overdesign

The assignment is about engineering and product thinking.

The UI should look polished enough to demonstrate product sense, but implementation time must remain focused on:
- agent execution;
- telemetry;
- observability;
- comparison.

### New dashboard panels
- **Code Impact:** lines added/removed, files touched, edits/session.
- **Workflow:** rework loops, corrections, abandoned runs, first-edit latency.
- **Tool Efficiency:** error rate and median latency.
- **Pricing Coverage:** percentage of usage with known pricing.
- **Execution Timeline:** expandable trace of user → LLM → tool → edit → result.

### Trust labels
Every metric should be labeled as one of:
- Provider reported
- Runtime measured
- Calculated
- Heuristic

This prevents a heuristic such as correction detection from being mistaken for a quality score.

### Comparison visualization
Do not use a single winner badge. Use side-by-side metrics and highlight observed differences. Suggested rows:
- outcome
- duration
- time to first edit
- LLM calls
- tool calls
- tool error rate
- median tool latency
- input/output/total tokens
- cache efficiency
- files touched
- edits
- lines added/removed
- output tokens/edit
- cost/edit
- cost/100 changed lines

## Final Feature Scope

The six core documents define the original AgentLens MVP. Only adopted features are included in these documents. Optional future enhancements are maintained separately in `07_RECOMMENDATIONS_FOR_FUTURE.md`.


---

# 05_BACKEND_SCHEMA.md

# AgentLens — Backend Schema Document

## 1. Schema Strategy

AgentLens uses two different storage systems for two different purposes:

### Supabase Postgres
For structured application and telemetry data.

### Chroma Cloud
For vectorized document chunks used by RAG.

Do not store embeddings in Postgres.

Do not store telemetry in Chroma.

---

## 2. Authentication Decision

Authentication is **not included in MVP**.

Instead, each browser installation creates an `installation_id`.

The frontend stores the identifier locally and sends it with API requests.

The backend associates executions with:
- installation_id;
- workspace_id;
- comparison_group_id.

This is sufficient for a single-user assignment/demo.

Future version:
- Supabase Auth;
- users;
- organizations;
- row-level security.

---

## 3. Core Entities

```text
installation
    |
    +---- workspace
              |
              +---- task
              |       |
              |       +---- execution
              |                |
              |                +---- llm_event
              |                +---- tool_event
              |                +---- rag_event
              |                +---- execution_event
              |
              +---- comparison_group
```

---

## 4. `installations`

Purpose:
Represent an anonymous browser installation.

Columns:

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| created_at | timestamptz | NOT NULL |
| last_seen_at | timestamptz | NOT NULL |
| metadata | jsonb | optional |

Do not store personally identifying information.

---

## 5. `workspaces`

Purpose:
Represent a logical agent workspace/demo repository.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| installation_id | UUID | FK |
| name | text | NOT NULL |
| type | text | NOT NULL |
| created_at | timestamptz | NOT NULL |
| metadata | jsonb | optional |

`type` examples:
- demo;
- uploaded;
- local.

Public deployment should primarily use `demo`.

---

## 6. `tasks`

Purpose:
Represent a user's requested task.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| installation_id | UUID | FK |
| workspace_id | UUID | FK |
| task_text | text | NOT NULL |
| task_type | text | NOT NULL |
| rag_enabled | boolean | NOT NULL |
| comparison_group_id | UUID | nullable |
| created_at | timestamptz | NOT NULL |

### Security
Task text may contain sensitive information.

Do not expose it through public analytics endpoints unless required.

---

## 7. `comparison_groups`

Purpose:
Group repeated executions of the same or intentionally equivalent task.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| installation_id | UUID | FK |
| name | text | NOT NULL |
| description | text | nullable |
| created_at | timestamptz | NOT NULL |

Example:
> "RAG policy summary — comparison"

---

## 8. `executions`

Purpose:
One complete agent run.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| task_id | UUID | FK |
| installation_id | UUID | FK |
| workspace_id | UUID | FK |
| comparison_group_id | UUID | nullable FK |
| provider | text | NOT NULL |
| model_id | text | NOT NULL |
| model_version | text | nullable |
| status | text | NOT NULL |
| started_at | timestamptz | NOT NULL |
| completed_at | timestamptz | nullable |
| duration_ms | bigint | nullable |
| llm_call_count | integer | default 0 |
| tool_call_count | integer | default 0 |
| retry_count | integer | default 0 |
| files_read_count | integer | default 0 |
| files_modified_count | integer | default 0 |
| command_count | integer | default 0 |
| rag_query_count | integer | default 0 |
| chunks_retrieved | integer | default 0 |
| tests_run | integer | default 0 |
| tests_passed | integer | default 0 |
| outcome | text | nullable |
| final_output | text | nullable |
| estimated_cost_usd | numeric | nullable |
| metadata | jsonb | optional |

Allowed status:
- queued;
- running;
- completed;
- failed;
- cancelled;
- timed_out.

Allowed outcome:
- success;
- partial;
- failed;
- unknown.

---

## 9. `llm_events`

Purpose:
One row per LLM invocation.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| execution_id | UUID | FK |
| sequence_no | integer | NOT NULL |
| provider | text | NOT NULL |
| model_id | text | NOT NULL |
| model_version | text | nullable |
| started_at | timestamptz | NOT NULL |
| completed_at | timestamptz | nullable |
| latency_ms | bigint | nullable |
| queue_time_ms | bigint | nullable |
| input_tokens | bigint | nullable |
| output_tokens | bigint | nullable |
| total_tokens | bigint | nullable |
| cached_tokens | bigint | nullable |
| reasoning_tokens | bigint | nullable |
| tool_tokens | bigint | nullable |
| usage_available | boolean | NOT NULL |
| input_cost_usd | numeric | nullable |
| output_cost_usd | numeric | nullable |
| estimated_cost_usd | numeric | nullable |
| pricing_version | text | nullable |
| status | text | NOT NULL |
| error_type | text | nullable |
| metadata | jsonb | optional |

Unknown usage must be NULL.

Never substitute zero when the provider did not return a field.

---

## 10. `tool_events`

Purpose:
Record every agent tool invocation.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| execution_id | UUID | FK |
| sequence_no | integer | NOT NULL |
| tool_name | text | NOT NULL |
| started_at | timestamptz | NOT NULL |
| completed_at | timestamptz | nullable |
| latency_ms | bigint | nullable |
| status | text | NOT NULL |
| retry_no | integer | default 0 |
| input_metadata | jsonb | nullable |
| output_metadata | jsonb | nullable |
| error_type | text | nullable |

Do not persist arbitrary raw command output unless needed.

---

## 11. `rag_events`

Purpose:
Record RAG retrieval operations.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| execution_id | UUID | FK |
| sequence_no | integer | NOT NULL |
| query_hash | text | nullable |
| top_k | integer | NOT NULL |
| result_count | integer | NOT NULL |
| retrieval_latency_ms | bigint | nullable |
| retrieved_chunk_count | integer | nullable |
| estimated_retrieved_tokens | bigint | nullable |
| context_selected_tokens | bigint | nullable |
| metadata | jsonb | optional |
| created_at | timestamptz | NOT NULL |

Avoid storing complete sensitive document content.

---

## 12. `execution_events`

Purpose:
Chronological high-level trace.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| execution_id | UUID | FK |
| sequence_no | integer | NOT NULL |
| event_type | text | NOT NULL |
| event_time | timestamptz | NOT NULL |
| summary | text | NOT NULL |
| metadata | jsonb | optional |

Examples:
- execution_started;
- llm_started;
- llm_completed;
- tool_started;
- tool_completed;
- rag_started;
- rag_completed;
- retry;
- execution_completed;
- execution_failed.

---

## 13. `model_pricing`

Purpose:
Store versioned provider pricing.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| provider | text | NOT NULL |
| model_id | text | NOT NULL |
| pricing_version | text | NOT NULL |
| input_usd_per_1m | numeric | nullable |
| output_usd_per_1m | numeric | nullable |
| effective_from | timestamptz | NOT NULL |
| effective_to | timestamptz | nullable |

Unique index:
- provider;
- model_id;
- pricing_version.

---

## 14. `model_catalog`

Purpose:
Control models displayed in the frontend.

| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| provider | text | NOT NULL |
| model_id | text | NOT NULL |
| display_name | text | NOT NULL |
| enabled | boolean | NOT NULL |
| context_window | integer | nullable |
| supports_tools | boolean | NOT NULL |
| supports_rag | boolean | NOT NULL |
| metadata | jsonb | optional |

Do not store provider secrets here.

---

## 15. Chroma Cloud Collections

Suggested collections:

### `agentlens_documents`

Metadata:
- document_id;
- filename;
- page;
- section;
- chunk_index;
- workspace_id.

### `agentlens_demo`

For preloaded demo documents.

---

## 16. Indexes

Recommended Postgres indexes:

### executions
- `installation_id`
- `created_at` via task/execution timestamps
- `model_id`
- `provider`
- `comparison_group_id`
- `status`

### llm_events
- `execution_id`
- `model_id`
- `provider`
- `started_at`

### tool_events
- `execution_id`
- `tool_name`
- `status`

### rag_events
- `execution_id`

### execution_events
- `execution_id`
- `(execution_id, sequence_no)`

---

## 17. Data Ownership

MVP:
- installation owns workspace/tasks/executions;
- comparison groups belong to installation;
- all execution data must be queryable only with the installation identifier.

Future:
- replace installation ownership with authenticated user/workspace ownership.

---

## 18. Analytics Queries

### Total tokens
Sum `llm_events.total_tokens`.

### Input tokens
Sum `llm_events.input_tokens`.

### Output tokens
Sum `llm_events.output_tokens`.

### Estimated cost
Sum `llm_events.estimated_cost_usd`.

### Tool success rate
successful `tool_events` / all `tool_events`.

### Average LLM calls
average `executions.llm_call_count`.

### Median duration
median `executions.duration_ms`.

### Model observed success rate
completed successful executions / completed executions for that model.

Label this:
> Observed success rate.

It is not a universal benchmark.

---

## 19. Derived Metric Rules

### Tokens per execution
Only use for descriptive reporting.

### Tokens per successful tool action
Useful for execution-level efficiency.

### Cost per successful execution
Useful only where success is objectively observable.

### Cost vs outcome
Show as a comparison, not a causal claim.

### Context utilization
Only calculate when both denominator and numerator are actually measurable.

---

## 20. No Fake Metrics

Never fabricate:
- token counts;
- costs;
- success percentages;
- context windows;
- tool efficiency;
- quality scores.

If data is unavailable:
> N/A

If a provider does not expose a metric:
> Not reported by provider

This is a core product trust principle.

### New first-class table: `edit_events`
Store:
- execution_id
- sequence_no
- file_path
- operation
- timestamp
- lines_added
- lines_removed
- changed_lines (nullable)
- content_size_before/after (nullable)
- is_repeat_file_edit

### New aggregate table: `file_activity`
Store per workspace/file:
- total edits
- total executions
- total lines added/removed
- first/last touched time

This supports cross-session churn and file heatmaps.

### New execution fields
Add:
- `time_to_first_edit_ms`
- `tool_error_count`
- `files_touched_count`
- `files_modified_count`
- `lines_added`
- `lines_removed`
- `edit_count`
- `correction_detected`
- `abandoned`

### Pricing fields
Support:
- input price
- output price
- cache-read price
- cache-write price
- pricing version

Unknown pricing remains NULL and is surfaced as unavailable.

## Final Feature Scope

The six core documents define the original AgentLens MVP. Only adopted features are included in these documents. Optional future enhancements are maintained separately in `07_RECOMMENDATIONS_FOR_FUTURE.md`.


---

# 06_IMPLEMENTATION_PLAN.md

# AgentLens — Implementation Plan

## 1. Implementation Objective

Build the smallest complete version of AgentLens that demonstrates:

1. A real tool-using AI agent.
2. Model selection outside the prompt.
3. Automatic LLM usage capture.
4. Tool execution telemetry.
5. RAG using hosted Chroma.
6. Persistent execution telemetry.
7. Two-page UI.
8. Observability analytics.
9. Manual same-task model comparison.
10. Vercel deployment.

Do not implement future features before the MVP workflow works.

---

# PHASE 0 — Project Setup

## Step 0.1 — Create repository

Repository:
`agentlens`

Structure:

```text
agentlens/
├── frontend/
├── backend/
├── docs/
├── sample_workspace/
├── tests/
├── .gitignore
├── README.md
└── package/project configuration
```

---

## Step 0.2 — Frontend

Create React + Vite + TypeScript.

Install:
- React Router if useful;
- Tailwind;
- Recharts;
- API client utilities.

Create:
- `AgentPage`
- `ObservabilityPage`
- shared layout;
- navigation.

Do not build detailed charts yet.

---

## Step 0.3 — Backend

Create FastAPI.

Initial routes:

```text
GET /api/health
GET /api/models
```

Verify frontend can reach backend.

---

# PHASE 1 — Data and Configuration

## Step 1.1 — Environment configuration

Create:

```text
GROQ_API_KEY
GEMINI_API_KEY
CHROMA_API_KEY
CHROMA_TENANT
CHROMA_DATABASE
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
```

Only configure the providers actually used.

---

## Step 1.2 — Model configuration

Create a configuration file or database-backed catalog.

Example:

```json
{
  "provider": "groq",
  "model_id": "MODEL_ID",
  "display_name": "Friendly Model Name",
  "enabled": true,
  "supports_tools": true
}
```

The frontend reads this from `/api/models`.

---

# PHASE 2 — LLM Gateway

## Step 2.1 — Define normalized response

Create:

```python
LLMResult
```

Fields:
- text;
- tool_calls;
- usage;
- provider;
- model;
- latency;
- raw metadata where safe.

---

## Step 2.2 — Provider adapter

Implement Groq first.

The adapter must:
1. send request;
2. receive response;
3. parse tool calls;
4. extract usage;
5. normalize usage;
6. return `LLMResult`.

Do not implement Gemini yet.

---

## Step 2.3 — Usage extraction tests

Create tests with mocked provider responses.

Verify:
- input tokens;
- output tokens;
- total tokens;
- cached tokens;
- timing;
- missing fields.

Important:
Unknown values must become `None`, not zero.

---

# PHASE 3 — Telemetry Engine

## Step 3.1 — Telemetry interface

Create:

```python
TelemetryRecorder
```

Methods:

```python
start_execution()
record_llm_start()
record_llm_complete()
record_tool_start()
record_tool_complete()
record_rag_event()
record_execution_event()
complete_execution()
fail_execution()
```

---

## Step 3.2 — LLM instrumentation

The LLM Gateway automatically records:
- model;
- usage;
- timing;
- cost;
- status.

The agent must not manually calculate token usage.

---

## Step 3.3 — Tool instrumentation

Create a wrapper:

```python
@instrument_tool("read_file")
```

or equivalent.

Every tool call automatically records:
- start;
- end;
- status;
- latency;
- retry.

---

# PHASE 4 — Agent Runtime

## Step 4.1 — Tool registry

Create tools:

```text
list_files
read_file
search_files
write_file
run_command
rag_search
```

---

## Step 4.2 — Agent loop

Implement:

```text
task
 ↓
LLM
 ↓
tool call?
 ├─ no → final
 └─ yes
      ↓
   execute tool
      ↓
   append result
      ↓
   LLM
```

Limit:
- 12 iterations.

---

## Step 4.3 — Agent safety

Implement:
- max iterations;
- tool timeouts;
- command allowlist;
- workspace boundary;
- output limits.

---

# PHASE 5 — Sample Workspace

Create a controlled demo project.

Example:

```text
sample_workspace/
├── README.md
├── data/
│   └── sales.csv
├── src/
│   ├── main.py
│   ├── utils.py
│   └── report.py
├── tests/
│   └── test_report.py
└── knowledge/
    ├── company_policy.md
    ├── product_guide.md
    └── sustainability.md
```

Create realistic but safe files.

---

# PHASE 6 — RAG

## Step 6.1 — Chroma Cloud

Create hosted collection.

Do not use local persistent Chroma for the deployed architecture.

---

## Step 6.2 — Ingestion

Implement:
- read documents;
- chunk;
- embed;
- store in Chroma Cloud.

Start with Markdown/TXT.

Add PDF only after the core flow works.

---

## Step 6.3 — Retrieval

Implement:

```python
rag_search(query, top_k)
```

Return:
- chunk ID;
- document;
- source metadata;
- text;
- score if available.

---

## Step 6.4 — RAG telemetry

Record:
- query;
- result count;
- retrieval latency;
- chunks retrieved;
- estimated context size.

---

# PHASE 7 — Database

## Step 7.1 — Supabase

Create free Supabase project.

Create tables according to Backend Schema.

At minimum implement:
- installations;
- tasks;
- comparison_groups;
- executions;
- llm_events;
- tool_events;
- execution_events;
- rag_events.

Model catalog and pricing can initially be config files if time is tight.

---

## Step 7.2 — Persistence

When an execution starts:
- create execution row.

During execution:
- write events.

At completion:
- update execution summary.

---

## Step 7.3 — Failure tolerance

If telemetry database insertion fails:
- do not crash the agent;
- log telemetry error;
- continue task execution.

---

# PHASE 8 — Agent Page

Build the complete Agent page.

Required controls:
- model dropdown;
- task type;
- task input;
- RAG toggle;
- knowledge base;
- comparison group;
- Run button.

Required output:
- agent messages;
- tool trace;
- final answer;
- execution fingerprint.

---

# PHASE 9 — Observability Page

## Step 9.1 — Summary cards

Implement:
- executions;
- LLM calls;
- total tokens;
- estimated cost;
- median duration.

---

## Step 9.2 — Token analytics

Charts:
- tokens by model;
- input vs output;
- token trend over time.

---

## Step 9.3 — Model analytics

Table:
- model;
- runs;
- observed success;
- average/median duration;
- average tokens;
- average cost.

---

## Step 9.4 — Tool analytics

Show:
- tool call count;
- success rate;
- retry count;
- average latency.

---

## Step 9.5 — Execution history

Columns:
- time;
- model;
- task type;
- status;
- LLM calls;
- tools;
- tokens;
- cost;
- duration.

Clicking a row opens execution detail.

---

# PHASE 10 — Comparison

## Step 10.1

Create comparison group UI.

## Step 10.2

Associate executions with group.

## Step 10.3

Build side-by-side comparison.

Required:
- model;
- outcome;
- duration;
- LLM calls;
- tools;
- retries;
- input tokens;
- output tokens;
- total tokens;
- cost;
- tool success;
- files;
- tests;
- RAG metrics.

Do not automatically rank the models.

---

# PHASE 11 — Innovation Layer

Only start after all MVP functionality works.

## Innovation 1 — Execution Fingerprint

Implement compact fingerprint card.

## Innovation 2 — Model Efficiency Profile

Show observed:
- median latency;
- average cost;
- average tokens;
- tool success;
- observed success.

## Innovation 3 — Context Efficiency

Show:
- retrieved;
- selected;
- sent;
- cached where available.

## Innovation 4 — Execution Trace

Make trace easy to inspect.

Do not add automatic model routing in V1.

---

# PHASE 12 — Testing

## Unit Tests

Test:
- usage normalization;
- cost calculation;
- telemetry recording;
- tool wrapper;
- analytics calculations.

---

## Agent Tests

Test:
1. simple Q&A;
2. file read;
3. file creation;
4. tool retry;
5. RAG query;
6. final response.

---

## Analytics Tests

Given fixed events, verify:

### Example

```text
Execution A
input = 1000
output = 500
total = 1500
```

Expected:
- total tokens = 1500.

Two executions:
- total = sum of both.

Tool success:
- successful / total.

Cost:
- calculated from configured pricing.

---

# PHASE 13 — Demo Scenarios

Prepare at least four polished scenarios.

## Scenario 1 — General Agent

Prompt:
> Explain the architecture of the sample workspace and identify the main execution path.

Expected:
- list/read/search tools;
- final answer;
- telemetry.

---

## Scenario 2 — Coding Task

Prompt:
> Create a Python utility that reads sales.csv and produces a summary report.

Expected:
- inspect files;
- create code;
- run validation;
- final result.

---

## Scenario 3 — RAG

Prompt:
> From the knowledge base, summarize the sustainability reporting requirements and cite the source documents.

Expected:
- RAG search;
- retrieved chunks;
- answer with sources;
- retrieval telemetry.

---

## Scenario 4 — Same Task Model Comparison

Create comparison group:
> "Sales utility comparison"

Run the exact same prompt twice.

Run A:
- select Model A.

Run B:
- select Model B.

Do not mention model names in the prompt.

Then compare:
- duration;
- LLM calls;
- tools;
- retries;
- input;
- output;
- total;
- cost;
- outcome;
- files;
- tests.

---

# PHASE 14 — Local Testing

Before deployment:

```text
Frontend
✓ starts
✓ Agent page works
✓ Observability works

Backend
✓ health endpoint
✓ model endpoint
✓ execution endpoint
✓ telemetry
✓ RAG
✓ database

Agent
✓ tool calls
✓ final response
✓ failure handling

Analytics
✓ data appears after run
✓ filters work
✓ comparison works
```

Do not deploy before these pass.

---

# PHASE 15 — Deployment

## Vercel

Deploy frontend/backend according to the Vercel FastAPI setup.

Configure environment variables.

Verify:
- frontend loads;
- backend is reachable;
- model call works;
- telemetry persists;
- Chroma Cloud works.

---

# PHASE 16 — Final Hardening

Check:
- no API keys in frontend;
- no API keys in Git;
- `.env` in `.gitignore`;
- no fake metrics;
- no broken demo links;
- no console errors;
- no missing loading states;
- no missing error states.

---

# PHASE 17 — Assignment Documentation

After implementation, create a separate assignment document covering:

1. What I built and why.
2. Problem definition.
3. Product hypothesis.
4. Architecture.
5. Key design decisions.
6. Why model selection is external to prompt.
7. Why telemetry is collected at LLM Gateway/tool boundaries.
8. Why raw tokens are not sufficient for task comparison.
9. Why objective execution metrics were chosen.
10. Why Chroma Cloud was selected.
11. Why Supabase Free was selected.
12. Trade-offs.
13. What was intentionally not built.
14. What I would build next.
15. What UI issues I observed in Superbrain.
16. What I would change/add and why.
17. Limitations and future research.

Keep this authentic and explain actual decisions made during development.

---

# 2-Day Priority Order

If time becomes limited, use this exact priority order:

### P0 — Must Work
1. FastAPI
2. React
3. Model selector
4. LLM Gateway
5. One provider
6. Agent loop
7. Tools
8. Telemetry
9. Observability page
10. Database persistence
11. RAG
12. Comparison
13. Local testing

### P1 — Important Polish
14. Tool analytics
15. Execution fingerprint
16. context metrics
17. model profile
18. second provider
19. SSE streaming

### P2 — Only if time remains
20. PDF ingestion improvements
21. export
22. advanced charts
23. additional providers
24. model recommendation
25. authentication

Never sacrifice P0 for P2.

---

# Final Build Rule

At every stage ask:

> "Does this improve the core demonstration: run an agent → observe its execution → understand model/tool/context usage → compare repeated runs?"

If the answer is no, defer the feature.

The finished product should be small, real, measurable, and explainable.

After the first working agent/telemetry vertical slice, implement observability in this order:

### 1. Code impact
Instrument `write_file` and any edit/patch operations. Capture old/new content where safe and calculate additions/removals. Add files touched, edits, output tokens/edit, cost/edit, and cost/100 changed lines.

### 2. Workflow signals
Implement:
- same-file rework loop;
- cross-execution file churn;
- explicit correction heuristic;
- abandoned execution;
- time to first edit;
- tool error rate;
- median tool latency;
- cache efficiency.

### 3. Session trajectory
Build the execution-detail timeline before advanced charts. Every aggregate metric should be traceable to underlying events.

### 4. Pricing coverage

### 5. Synthetic demo data

### 6. Future local transcript adapters

## Revised P0/P1/P2 Priority

### P0
- real agent
- model dropdown
- LLM Gateway
- one provider
- tool runtime
- LLM usage telemetry
- execution trace
- Supabase persistence
- code-impact instrumentation
- Observability page
- one RAG workflow
- manual same-task comparison
- Vercel deployment

### P1
- workflow signals
- pricing coverage
- context/cache analytics
- second provider
- richer charts
- synthetic sample mode

### P2
- external JSONL adapters
- local/private mode
- export
- automatic model routing
- authentication

## Final Feature Scope

The six core documents define the original AgentLens MVP. Only adopted features are included in these documents. Optional future enhancements are maintained separately in `07_RECOMMENDATIONS_FOR_FUTURE.md`.


---

# 07_RECOMMENDATIONS_FOR_FUTURE.md

# AgentLens — Recommendations for Future

These are **optional enhancements**. They must not block the assignment MVP.

## How to use this document

Priority order:

1. Finish all six core AgentLens documents and their adopted features.
2. Test the complete product locally.
3. Deploy successfully.
4. Only then consider these recommendations.
5. Stop immediately if an enhancement threatens the submission deadline.

---

## 1. External Agent Adapters

### Idea

Allow AgentLens to analyze agents that it does not execute itself.

Potential sources:
- Claude Code;
- Codex-style CLI agents;
- OpenClaw-style agents;
- other agents exposing structured logs.

### Proposed architecture

```text
External Agent
      ↓
JSONL / structured transcript
      ↓
Source Adapter
      ↓
Normalized AgentLens Events
      ↓
Same Analytics Engine
```

### Why it is useful

It would extend AgentLens from a live-agent observability tool into a broader agent observability platform.

### Why it is not MVP

Our assignment requires a working project in a very short time. The live-agent architecture already produces telemetry directly, so external adapters are unnecessary for the core demonstration.

---

## 2. JSONL Import / Analysis

### Idea

Add an import workflow:

```text
Upload JSONL
     ↓
Parse
     ↓
Normalize
     ↓
Analyze
```

This is especially useful for transcript-based agents.

### Possible UI

```text
Observability
  → Import External Run
  → Upload JSONL
  → Select source
  → Analyze
```

### Benefit

Makes the analytics engine reusable beyond AgentLens's own agent.

---

## 3. Local / Private Analytics Mode

### Idea

Offer a mode where telemetry stays entirely on the user's machine.

Possible architecture:

```text
Agent
 ↓
JSONL / local SQLite
 ↓
Local Analytics
 ↓
Local Dashboard
```

### Benefit

Useful for sensitive coding environments where prompts, file names, and tool traces should not leave the machine.

### Recommendation

Consider this only after the deployed MVP is stable.

---

## 4. Expanded Model Efficiency Profiles

The MVP already compares manually repeated runs.

A future version could create richer profiles across many executions:

```text
MODEL A

Median duration
Median tool calls
Tool error rate
Cache efficiency
Edits/session
Cost/edit
Cost/100 changed lines
RAG retrieval behavior
```

The profile should always be labeled:

> Based on observed executions

It should not become a universal benchmark score.

---

## 5. More Advanced Correction Detection

The MVP can use a simple heuristic.

A future version could classify corrections more carefully:

- explicit factual correction;
- requirement change;
- formatting correction;
- code correction;
- scope change;
- user clarification.

This would make the workflow metric more informative.

---

## 6. Richer Context Analytics

Future versions could distinguish:

- requested context;
- retrieved context;
- selected context;
- sent context;
- cached context;
- context-window utilization.

This could help investigate whether agents are inefficient because of excessive context rather than model reasoning.

---

## 7. Adapter / Normalization SDK

A future developer SDK could expose:

```python
from agentlens import observe

observe.llm(...)
observe.tool(...)
observe.edit(...)
observe.rag(...)
```

External agents could then emit normalized AgentLens events without implementing the complete analytics system.

---

## 8. OpenTelemetry Integration

AgentLens could eventually export normalized traces using OpenTelemetry concepts.

Potential architecture:

```text
Agent
 ↓
AgentLens Events
 ↓
OpenTelemetry
 ↓
External Observability Stack
```

This would make AgentLens interoperable with existing engineering observability infrastructure.

---

## 9. Model Recommendation Layer

Once sufficient execution history exists, AgentLens could make workload-specific recommendations.

For example:

> For similar RAG coding tasks, Model B has lower median latency and lower observed cost per successful execution.

Important:

The recommendation should be based on the user's observed workload, not a universal model ranking.

---

## 10. Subscription / Plan Economics

A future product could compare:

- API-equivalent cost;
- subscription cost;
- usage volume;
- effective cost per successful execution.

This is outside the assignment's core observability use case but could become a useful product extension.

---

## 11. Advanced Benchmarking

With a larger dataset and controlled tasks, AgentLens could support:

- benchmark suites;
- repeated trials;
- statistical summaries;
- regression detection;
- model version comparison.

This requires substantially more experimental rigor than the assignment MVP.

---

## 12. Feature Decision Summary

| Feature | Current decision | Future recommendation |
|---|---|---|
| External agent adapters | MODIFY | Optional |
| JSONL import | MODIFY | Optional |
| Local/private mode | MODIFY | Optional |
| Rich model profiles | MODIFY | Optional |
| Advanced correction detection | MODIFY | Optional |
| Rich context analytics | MODIFY | Optional |
| AgentLens instrumentation SDK | MODIFY | Optional |
| OpenTelemetry | MODIFY | Optional |
| Workload-specific recommendations | MODIFY | Optional |
| Subscription economics | MODIFY | Optional |
| Advanced benchmarking | MODIFY | Optional |

---

## Final rule

Do not start any recommendation until the six core documents are implemented, tested, and deployed.

The assignment submission must remain complete without any item in this document.
