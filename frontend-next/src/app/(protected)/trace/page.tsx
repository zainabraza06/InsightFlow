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

interface TraceFile {
  session_id: string;
  scenario: string;
  started_at: string;
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
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-xl font-bold text-white">Antigravity Trace Viewer</h1>
              <p className="text-sm text-gray-500 mt-1">Load a trace JSON to inspect orchestration events</p>
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
            <Card className="p-16 text-center">
              <p className="text-4xl mb-4">🛸</p>
              <p className="text-gray-400">Load an antigravity_trace.json file to inspect events</p>
              <p className="text-xs text-gray-600 mt-2">Run <code className="text-nexus-cyan font-mono">python antigravity_orchestrator.py supply</code> to generate one</p>
            </Card>
          )}

          {trace && (
            <>
              {/* Header */}
              <Card className="p-4 mb-4 flex items-center gap-6 text-sm font-mono">
                <div>
                  <span className="text-gray-500">Session: </span>
                  <span className="text-nexus-cyan">{trace.session_id?.slice(0, 8)}…</span>
                </div>
                <div>
                  <span className="text-gray-500">Scenario: </span>
                  <span className="text-white">{trace.scenario}</span>
                </div>
                <div>
                  <span className="text-gray-500">Events: </span>
                  <span className="text-nexus-green">{trace.events?.length}</span>
                </div>
                <div>
                  <span className="text-gray-500">Started: </span>
                  <span className="text-gray-300">{new Date(trace.started_at).toLocaleString()}</span>
                </div>
              </Card>

              {/* Filter */}
              <div className="flex gap-2 mb-4 flex-wrap">
                {["ALL", ...allTypes].map((t) => (
                  <button
                    key={t}
                    onClick={() => setFilter(t)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${filter === t ? "bg-nexus-cyan text-black" : "border border-nexus-border text-gray-500 hover:border-nexus-cyan hover:text-nexus-cyan"}`}
                  >
                    {t}
                  </button>
                ))}
              </div>

              {/* Events timeline */}
              <div className="space-y-2">
                {filtered.map((event) => (
                  <Card key={event.seq} className="p-4">
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
                          <p className="mt-1 text-xs text-gray-500 italic">{event.reasoning}</p>
                        )}
                        {event.data && Object.keys(event.data).length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs text-nexus-cyan cursor-pointer hover:underline">Data payload</summary>
                            <pre className="mt-1 text-[10px] font-mono text-gray-500 overflow-x-auto max-h-40 p-2 bg-black/20 rounded">
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
