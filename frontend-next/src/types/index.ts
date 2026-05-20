export interface User {
  name: string;
  email: string;
  is_admin?: boolean;
}

export interface AuthState {
  user: User | null;
  token: string | null;
}

export interface Source {
  source_type: string;
  content: string;
  credibility_score: number;
  word_count?: number;
}

export interface Contradiction {
  contradiction_type?: "internal" | "cross_source";
  conflict: string;
  sources: string[];
  severity: string;
}

export interface IngestResult {
  sources_processed: number;
  sources_trusted: number;
  sources_excluded: number;
  credibility_map: Record<string, number>;
  contradictions_found: number;
  internal_contradictions_found?: number;
  cross_source_contradictions_found?: number;
  contradictions: { contradictions: Contradiction[]; temporal_analysis: Record<string, unknown> };
  temporal_analysis: Record<string, unknown>;
  noise_filtered: string[];
  ready_for_analysis: boolean;
}

export interface AgentResult {
  agent: string;
  role: string;
  insight: string;
  confidence: number;
  key_risks?: string[];
  recommendations?: string[];
}

export interface ActionItem {
  step: number;
  action: string;
  rationale: string;
  estimated_cost_pkr: number;
  estimated_time_minutes: number;
  side_effect: string;
  monitor: string;
  was_modified: boolean;
  constraint_note?: string;
  status?: string;
  real_result?: Record<string, unknown>;
}

export interface AnalyzeResult {
  agents: AgentResult[];
  resolved: {
    final_insight: string;
    confidence: number;
    contradiction_resolution: string;
  };
  action_chain: ActionItem[];
  consensus_confidence: number;
  weighted_confidence?: number;
  debate_rounds: number;
  constraints_applied: Record<string, unknown>;
  learning_active?: boolean;
  learning_context?: {
    has_feedback: boolean;
    avg_rating?: number;
    total_feedback?: number;
    sentiment?: string;
    negative_comments?: string[];
    positive_comments?: string[];
  };
}

export interface ExecuteResult {
  chain: ActionItem[];
  before_state: Record<string, unknown>;
  after_state: Record<string, unknown>;
  total_cost_pkr: number;
  total_latency_ms: number;
  failures: number;
  recovered: number;
  log: Array<{ timestamp: string; time_display: string; message: string }>;
}

export interface WhatIfResult {
  what_if_constraints: Record<string, unknown>;
  modifications_applied: Record<string, unknown>;
  action_chain: ActionItem[];
  total_estimated_cost_pkr: number;
  total_estimated_time_minutes: number;
  actions_modified: number;
  cost_delta_pkr: number;
  feasibility_summary: string;
}

export interface HistoryEntry {
  id: string;
  timestamp: string;
  domain: string;
  topic: string;
  sources_processed: number;
  contradictions_found: number;
  actions_total: number;
  total_cost_pkr: number;
  status: string;
}

export interface HistoryDetail extends HistoryEntry {
  ingest_result?: IngestResult;
  analyze_result?: AnalyzeResult;
  execute_result?: ExecuteResult;
}

export type Domain = "Business" | "Healthcare" | "Supply Chain" | "Agriculture" | "Finance" | "Government";

export interface Constraints {
  budget_pkr: number;
  max_response_time_hours: number;
  max_staff: number;
  urgency: "low" | "medium" | "high" | "critical";
}
