"use client";
import { useState } from "react";
import Navbar from "@/components/layout/Navbar";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { exportTrace } from "@/lib/api";

const EVENT_COLORS: Record<string, "cyan" | "purple" | "green" | "amber" | "gray"> = {
  WORKPLAN: "cyan",
  TASK_PLAN: "cyan",
  PHASE: "purple",
  TOOL_CALL: "amber",
  TOOL_RESULT: "green",
  REASONING: "gray",
  DECISION: "purple",
  RECOVERY: "amber",
  OUTCOME: "green",
};

interface TraceEvent {
  seq: number;
  event_type: string;
  timestamp: string;
  description: string;
  reasoning?: string;
  data?: Record<string, unknown>;
}

interface Workplan {
  objective: string;
  phases: string[];
  tools_registered: string[];
  constraints: {
    max_budget_pkr: number;
    max_response_time_hours: number;
    available_staff: number;
    urgency_level: string;
  };
  success_criteria: string;
}

interface TaskPlanItem {
  step: number;
  task: string;
  tool: string;
  depends_on: number | null;
  expected_output: string;
}

interface TraceFile {
  schema?: string;
  system?: string;
  orchestrator?: string;
  session_id: string;
  scenario: string;
  started_at: string;
  completed_at?: string;
  total_events?: number;
  workplan?: Workplan;
  task_plan?: TaskPlanItem[];
  events: TraceEvent[];
}

export default function TracePage() {
  const [trace, setTrace] = useState<TraceFile | null>(null);
  const [filter, setFilter] = useState("ALL");
  const [error, setError] = useState("");

  function loadFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const data = JSON.parse(ev.target?.result as string);
        setTrace(data);
        setError("");
      } catch {
        setError("Invalid JSON file");
      }
    };
    reader.readAsText(file);
  }

  const allTypes = trace ? Array.from(new Set(trace.events.map((e) => e.event_type))) : [];
  const filtered = trace
    ? filter === "ALL"
      ? trace.events
      : trace.events.filter((e) => e.event_type === filter)
    : [];

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Navbar />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto pb-12">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <span>🛸</span> NEXUS Execution Trace
              </h1>
              <p className="text-sm text-gray-500 mt-1">Inspect the 5-agent pipeline — phases, tool calls, reasoning, and execution events</p>
            </div>
            <div className="flex gap-3">
              <label className="cursor-pointer">
                <span className="px-4 py-2 rounded-lg border border-nexus-border text-sm text-gray-400 hover:border-nexus-cyan hover:text-nexus-cyan transition-all">
                  Load Trace File
                </span>
                <input type="file" accept=".json" className="hidden" onChange={loadFile} />
              </label>
              <Button variant="outline" size="sm" onClick={() => exportTrace()}>
                Export Current
              </Button>
            </div>
          </div>

          {error && (
            <div className="p-4 mb-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              {error}
            </div>
          )}

          {!trace && (
            <div className="space-y-6">
              {/* Global IDE Context Banner */}
              <Card className="p-4 border-l-2 border-l-nexus-amber bg-nexus-amber/5">
                <div className="flex items-start gap-3 text-xs">
                  <span className="text-nexus-amber font-bold text-sm shrink-0">💡</span>
                  <div>
                    <p className="font-semibold text-white mb-1">Developer Workspace Context (IDE vs. Runtime)</p>
                    <p className="text-gray-400 leading-relaxed">
                      NEXUS was engineered inside the <strong>Antigravity AI IDE</strong> workspace. While the live runtime 
                      agents are orchestrated standalone using the <strong>Google Agent Development Kit (ADK)</strong> and 
                      Gemini models, the system produces traces matching our development workplan in{" "}
                      <a href="file:///e:/MERN/PROJECTS/aiseekho/PLAN.md" className="text-nexus-cyan hover:underline font-mono">
                        PLAN.md
                      </a>{" "}
                      to provide a comprehensive audit track for evaluation.
                    </p>
                  </div>
                </div>
              </Card>

              <Card className="p-16 text-center">
                <p className="text-4xl mb-4">🛸</p>
                <p className="text-gray-400">Load a NEXUS trace JSON to inspect agent pipeline events</p>
                <p className="text-xs text-gray-600 mt-2">Click <strong className="text-nexus-cyan">Export Current</strong> on the Dashboard after a run, or load <code className="text-nexus-cyan font-mono">antigravity_trace.json</code> from the project root.</p>
              </Card>
            </div>
          )}

          {trace && (
            <>
              {/* Active IDE Context Card */}
              <Card className="p-4 mb-6 border-l-2 border-l-nexus-amber bg-nexus-amber/5">
                <div className="flex items-start gap-3 text-xs">
                  <span className="text-nexus-amber font-bold text-sm shrink-0">💡</span>
                  <div>
                    <p className="font-semibold text-white mb-1">Developer Workspace Context (IDE vs. Runtime)</p>
                    <p className="text-gray-400 leading-relaxed">
                      This Trace Viewer visualizes execution logs exported from your run inside the <strong>Antigravity AI IDE</strong> workspace. 
                      While the standalone application's runtime agents are orchestrated using the <strong>Google Agent Development Kit (ADK)</strong>, 
                      this trace validates that our runtime execution mirrors the exact task dependencies and phases designed in{" "}
                      <a href="file:///e:/MERN/PROJECTS/aiseekho/PLAN.md" className="text-nexus-cyan hover:underline font-mono">
                        PLAN.md
                      </a>.
                    </p>
                  </div>
                </div>
              </Card>

              {/* Orchestrator Metadata HUD */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <Card className="p-4 border-l-2 border-l-nexus-cyan">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Runtime Agent Stack</p>
                  <div className="space-y-1 text-xs font-mono">
                    <p className="text-gray-400">System: <span className="text-white">{trace.system || "NEXUS"}</span></p>
                    <p className="text-gray-400">Runtime: <span className="text-nexus-cyan font-bold">Google ADK + Gemini 2.0 Flash</span></p>
                    <p className="text-gray-400">Dev IDE: <span className="text-nexus-amber">Antigravity AI</span></p>
                    <p className="text-gray-400">Session ID: <span className="text-gray-300">{trace.session_id}</span></p>
                  </div>
                </Card>

                <Card className="p-4 border-l-2 border-l-nexus-purple">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Execution Metrics</p>
                  <div className="space-y-1 text-xs font-mono">
                    <p className="text-gray-400">Scenario: <span className="text-white">{trace.scenario}</span></p>
                    <p className="text-gray-400">Started At: <span className="text-gray-300">{trace.started_at ? new Date(trace.started_at).toLocaleString() : "-"}</span></p>
                    {trace.completed_at && (
                      <p className="text-gray-400">Completed At: <span className="text-gray-300">{new Date(trace.completed_at).toLocaleString()}</span></p>
                    )}
                    <p className="text-gray-400">Total Log Entries: <span className="text-nexus-green font-bold">{trace.events?.length || 0}</span></p>
                  </div>
                </Card>
              </div>

              {/* Workplan Summary (Antigravity Objective & Phases) */}
              {trace.workplan && (
                <Card className="p-5 mb-6 bg-nexus-cyan/5 border border-nexus-cyan/20">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-nexus-cyan font-bold text-sm">🎯</span>
                    <span className="text-sm font-semibold text-white uppercase tracking-wider">NEXUS Agent Pipeline — Workplan</span>
                  </div>
                  
                  <div className="mb-4">
                    <p className="text-xs text-gray-500 uppercase font-mono tracking-wider">Active Objective</p>
                    <p className="text-sm text-gray-200 mt-1 font-sans">{trace.workplan.objective}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <p className="text-xs text-gray-500 uppercase font-mono tracking-wider mb-2">7-Phase Execution Timeline</p>
                      <div className="space-y-1.5">
                        {trace.workplan.phases.map((phase, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-xs">
                            <span className="text-nexus-cyan font-mono select-none shrink-0">{idx + 1}.</span>
                            <span className="text-gray-300">{phase.replace(/^Phase\s\d+\s—\s/, "")}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="flex flex-col justify-between">
                      <div>
                        <p className="text-xs text-gray-500 uppercase font-mono tracking-wider mb-2">Target Constraints</p>
                        <div className="space-y-1 text-xs font-mono">
                          {trace.workplan.constraints && (
                            <>
                              <p className="text-gray-400">Max Budget: <span className="text-nexus-amber">PKR {trace.workplan.constraints.max_budget_pkr.toLocaleString()}</span></p>
                              <p className="text-gray-400">Response SLA: <span className="text-white">{trace.workplan.constraints.max_response_time_hours} hours</span></p>
                              <p className="text-gray-400">Staff Limit: <span className="text-white">{trace.workplan.constraints.available_staff} agents</span></p>
                              <p className="text-gray-400">Urgency: <span className="text-nexus-red">{trace.workplan.constraints.urgency_level.toUpperCase()}</span></p>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="mt-4 pt-4 border-t border-nexus-border/30">
                        <p className="text-xs text-gray-500 uppercase font-mono tracking-wider">Success Criteria</p>
                        <p className="text-xs text-nexus-green mt-0.5">{trace.workplan.success_criteria}</p>
                      </div>
                    </div>
                  </div>
                </Card>
              )}

              {/* Task Plan Dependency Tree */}
              {trace.task_plan && trace.task_plan.length > 0 && (
                <Card className="p-5 mb-6">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="text-nexus-purple font-bold text-sm">⛓️</span>
                    <span className="text-sm font-semibold text-white uppercase tracking-wider">Orchestrated Task Dependency Map</span>
                  </div>
                  <div className="space-y-2">
                    {trace.task_plan.map((item) => (
                      <div key={item.step} className="p-3 rounded bg-white/3 border border-nexus-border/30 text-xs flex items-center justify-between gap-4 font-mono">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="px-1.5 py-0.5 rounded bg-nexus-cyan/10 border border-nexus-cyan/30 text-nexus-cyan text-[10px] font-bold">STEP {item.step}</span>
                            <span className="text-white truncate font-sans font-semibold">{item.task}</span>
                          </div>
                          <p className="text-gray-500 text-[10px]">Expects: <span className="text-gray-300">{item.expected_output}</span></p>
                        </div>
                        <div className="text-right shrink-0">
                          <span className="px-2 py-1 rounded bg-black/35 border border-nexus-border text-gray-400 text-[10px]">{item.tool}</span>
                          {item.depends_on !== null && (
                            <p className="text-[9px] text-nexus-amber mt-1">Requires Step {item.depends_on}</p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              )}

              {/* Filters */}
              <div className="flex gap-2 mb-4 items-center justify-between">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Trace Log Stream</span>
                <div className="flex gap-1.5 flex-wrap">
                  {["ALL", ...allTypes].map((t) => (
                    <button
                      key={t}
                      onClick={() => setFilter(t)}
                      className={`px-3 py-1.5 rounded-lg text-[10px] font-mono font-semibold transition-all ${filter === t ? "bg-nexus-cyan text-black" : "border border-nexus-border text-gray-500 hover:border-nexus-cyan hover:text-nexus-cyan"}`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {/* Events timeline */}
              <div className="space-y-2">
                {filtered.map((event) => (
                  <Card key={event.seq} className="p-4 hover:border-nexus-border-cyan transition-all">
                    <div className="flex items-start gap-3">
                      <span className="w-8 text-right text-[10px] font-mono text-gray-600 shrink-0 mt-0.5">
                        #{event.seq}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant={EVENT_COLORS[event.event_type] ?? "gray"}>{event.event_type}</Badge>
                          <span className="text-xs text-gray-600 font-mono">
                            {new Date(event.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-sm text-white">{event.description}</p>
                        {event.reasoning && (
                          <p className="mt-1.5 text-xs text-gray-400 italic bg-white/5 border border-nexus-border/20 px-3 py-2 rounded-lg font-mono">
                            <span className="text-nexus-cyan font-bold not-italic mr-1">Reasoning:</span> {event.reasoning}
                          </p>
                        )}
                        {event.data && Object.keys(event.data).length > 0 && (
                          <details className="mt-3">
                            <summary className="text-xs text-nexus-cyan cursor-pointer hover:underline font-mono select-none">Show Data Payload</summary>
                            <pre className="mt-2 text-[10px] font-mono text-gray-500 overflow-x-auto max-h-60 p-3 bg-black/35 border border-nexus-border/50 rounded-lg">
                              {JSON.stringify(event.data, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
