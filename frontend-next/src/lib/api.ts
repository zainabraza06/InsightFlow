import type { IngestResult, AnalyzeResult, ExecuteResult, WhatIfResult, HistoryEntry, HistoryDetail, Constraints } from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeader(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("nexus_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { ...authHeader(), ...init?.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────────

export const authApi = {
  register: (name: string, email: string, password: string) =>
    request<{ token: string; user: { name: string; email: string } }>("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    }),
  login: (email: string, password: string) =>
    request<{ token: string; user: { name: string; email: string } }>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<{ name: string; email: string }>("/auth/me"),
  updateProfile: (data: { name?: string; password?: string }) =>
    request<{ name: string; email: string }>("/auth/me", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
};

// ── Core NEXUS ───────────────────────────────────────────────────

export async function ingest(formData: FormData): Promise<IngestResult> {
  const res = await fetch(`${BASE}/ingest`, {
    method: "POST",
    headers: authHeader(),
    body: formData,
  });
  if (!res.ok) throw new Error(`Ingest failed: ${res.status}`);
  return res.json();
}

export async function analyze(domain: string, constraints?: Partial<Constraints>): Promise<AnalyzeResult> {
  return request<AnalyzeResult>("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ domain, constraints }),
  });
}

export async function execute(chain?: unknown[], domain?: string): Promise<ExecuteResult> {
  return request<ExecuteResult>("/execute", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chain, domain }),
  });
}

export async function whatIf(modifications: Record<string, unknown>): Promise<WhatIfResult> {
  return request<WhatIfResult>("/what-if", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ modifications }),
  });
}

export async function getState() {
  return request<Record<string, unknown>>("/state");
}

export async function getLogs() {
  return request<{ logs: Array<{ timestamp: string; time_display: string; message: string }> }>("/logs");
}

export async function getBaselineComparison() {
  return request<Record<string, unknown>>("/baseline-comparison");
}

export async function exportTrace(): Promise<void> {
  const res = await fetch(`${BASE}/export-trace`, { headers: authHeader() });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "nexus_antigravity_trace.json";
  a.click();
  URL.revokeObjectURL(url);
}

// ── Feedback ──────────────────────────────────────────────────────

export const feedbackApi = {
  submit: (data: {
    rating: number;
    domain: string;
    comment?: string;
    analysis_id?: string;
    agent_confidences?: Record<string, number>;
  }) =>
    request<{ id: string; saved: boolean; learning_context: Record<string, unknown> }>("/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
  stats: () => request<Record<string, unknown>>("/feedback/stats"),
  myFeedback: () => request<unknown[]>("/feedback/my"),
  domainContext: (domain: string) =>
    request<Record<string, unknown>>(`/feedback/domain/${encodeURIComponent(domain)}`),
};

// ── History ───────────────────────────────────────────────────────

export const historyApi = {
  save: (entry: Record<string, unknown>) =>
    request<{ id: string; saved: boolean }>("/history", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry),
    }),
  list: () => request<HistoryEntry[]>("/history"),
  get: (id: string) => request<HistoryDetail>(`/history/${id}`),
  delete: (id: string) =>
    request<{ deleted: boolean }>(`/history/${id}`, { method: "DELETE" }),
};

// ── Admin ─────────────────────────────────────────────────────────

export const adminApi = {
  users: () => request<Array<{ name: string; email: string; is_admin: boolean }>>("/admin/users"),
  history: () => request<any[]>("/admin/history"),
  feedback: () => request<any[]>("/admin/feedback"),
  stats: () => request<{
    total_users: number;
    total_runs: number;
    total_feedback: number;
    avg_rating: number;
    total_cost_spent: number;
    domain_stats: Record<string, { runs: number; cost: number }>;
  }>("/admin/dashboard-stats"),
};
