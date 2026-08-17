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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Installation-Id": getInstallationId(),
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
    } catch {
      detail = await response.text();
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return response.json() as Promise<T>;
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
  uploads: () => request<{ files: { name: string; path: string; bytes: number }[] }>("/api/uploads"),
  upload: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const response = await fetch("/api/uploads", {
      method: "POST",
      headers: { "X-Installation-Id": getInstallationId() },
      body: form,
    });
    if (!response.ok) {
      let detail = response.statusText;
      try {
        const body = await response.json();
        detail = body.detail || JSON.stringify(body);
      } catch {
        detail = await response.text();
      }
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return response.json() as Promise<{ name: string; path: string; bytes: number }>;
  },
};
