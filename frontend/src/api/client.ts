import type {
  ComparisonGroup,
  ExecutionDetail,
  HistoryRow,
  ModelOption,
  ModelProfile,
  Overview,
  ToolRow,
} from "../types";

const INSTALL_KEY = "agentlens_installation_id";

export function getInstallationId(): string {
  const existing = localStorage.getItem(INSTALL_KEY);
  if (existing) return existing;
  const id = crypto.randomUUID();
  localStorage.setItem(INSTALL_KEY, id);
  return id;
}

async function readBody(response: Response): Promise<unknown> {
  const raw = await response.text();
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

function errorMessage(body: unknown, response: Response): string {
  if (typeof body === "string" && body.trim()) return body;
  if (body && typeof body === "object") {
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (detail !== undefined) return JSON.stringify(detail);
    return JSON.stringify(body);
  }
  if (response.status === 502 || response.status === 503) {
    return "The backend is waking up or temporarily down. Wait about a minute and try again.";
  }
  return response.statusText || `Request failed (${response.status})`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Installation-Id": getInstallationId(),
      ...(init?.headers || {}),
    },
  });
  const body = await readBody(response);
  if (!response.ok) {
    throw new Error(errorMessage(body, response));
  }
  return body as T;
}

export const api = {
  health: () => request<{ status: string; openai_configured: boolean; groq_configured: boolean }>("/api/health"),
  models: () => request<{ models: ModelOption[] }>("/api/models"),
  startExecution: (payload: {
    task: string;
    model: { provider: string; model_id: string };
    task_type: string;
    comparison_group_id: string | null;
    rag_enabled: boolean;
    workspace_id: string;
  }) => request<{ execution_id: string; status: string }>("/api/executions", { method: "POST", body: JSON.stringify(payload) }),
  stopExecution: (id: string) =>
    request<{ execution_id: string; status: string }>(`/api/executions/${id}/stop`, { method: "POST" }),
  execution: (id: string) => request<ExecutionDetail>(`/api/executions/${id}`),
  events: (id: string) =>
    request<{
      execution_id: string;
      status: string;
      fingerprint: HistoryRow;
      events: ExecutionDetail["events"];
      final_output: string | null;
      outcome: string | null;
    }>(`/api/executions/${id}/events`),
  groups: () => request<{ groups: ComparisonGroup[] }>("/api/comparison-groups"),
  createGroup: (name: string, description?: string) =>
    request<ComparisonGroup>("/api/comparison-groups", { method: "POST", body: JSON.stringify({ name, description }) }),
  overview: (query: string) => request<Overview>(`/api/analytics/overview${query}`),
  modelAnalytics: (query: string) => request<{ models: ModelProfile[] }>(`/api/analytics/models${query}`),
  toolAnalytics: (query: string) => request<{ tools: ToolRow[] }>(`/api/analytics/tools${query}`),
  history: (query: string) => request<{ executions: HistoryRow[] }>(`/api/analytics/history${query}`),
  comparison: (id: string) => request<{ group: ComparisonGroup | null; table: { metric: string; runs: unknown[] }[]; executions: HistoryRow[]; note: string }>(`/api/analytics/comparisons/${id}`),
  uploads: () =>
    request<{
      files: { name: string; path: string; bytes: number }[];
      uploads?: { name: string; path: string; bytes: number }[];
      builtin?: { name: string; path: string; bytes: number }[];
    }>("/api/uploads"),
  deleteUpload: (name: string) =>
    request<{ deleted: string; path: string }>(`/api/uploads/${encodeURIComponent(name)}`, { method: "DELETE" }),
  upload: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const response = await fetch("/api/uploads", {
      method: "POST",
      headers: { "X-Installation-Id": getInstallationId() },
      body: form,
    });
    const body = await readBody(response);
    if (!response.ok) {
      throw new Error(errorMessage(body, response));
    }
    return body as { name: string; path: string; bytes: number };
  },
};
