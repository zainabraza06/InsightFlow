"use client";
import { useState, useRef } from "react";
import Navbar from "@/components/layout/Navbar";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import { Textarea, Input } from "@/components/ui/Input";
import AgentDebate from "@/components/analysis/AgentDebate";
import ActionChain from "@/components/analysis/ActionChain";
import RiskTimeline from "@/components/analysis/RiskTimeline";
import FeedbackWidget from "@/components/analysis/FeedbackWidget";
import { ingest, analyze, execute, whatIf, exportTrace, historyApi } from "@/lib/api";
import type { IngestResult, AnalyzeResult, ExecuteResult, WhatIfResult } from "@/types";

const DOMAINS = ["Business", "Healthcare", "Supply Chain", "Agriculture", "Finance", "Government"];
const SEEDS = [
  { label: "Supply Chain", domain: "Supply Chain", text: "Karachi port congestion delays 200 containers. Vendor claims 3-day delay. Regulatory data shows 2-week backlog. Industry report contradicts vendor optimism." },
  { label: "Hospital", domain: "Healthcare", text: "Insulin shortage at major hospital. Vendor confirms shipment next week. WHO report flags global shortage. Patient records show critical inventory at 4-day supply." },
  { label: "Agri Export", domain: "Agriculture", text: "Punjab wheat export ban lifted. Government press release claims surplus. Ground reports from district agriculture show 30% below target yield due to flooding." },
];
const WHATIF_PRESETS = [
  { label: "Budget ×2", mod: { budget_pkr: 1000000 } },
  { label: "Budget ÷2", mod: { budget_pkr: 250000 } },
  { label: "Crisis Mode", mod: { urgency: "critical", max_response_time_hours: 1 } },
  { label: "Minimal Staff", mod: { max_staff: 1 } },
];

type Step = "idle" | "ingesting" | "ingested" | "analyzing" | "analyzed" | "executing" | "done";

export default function DashboardPage() {
  const [step, setStep] = useState<Step>("idle");
  const [domain, setDomain] = useState("Business");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [csv, setCsv] = useState("");
  const [includeFeed, setIncludeFeed] = useState(false);
  const [topic, setTopic] = useState("");

  const [ingestResult, setIngestResult] = useState<IngestResult | null>(null);
  const [analyzeResult, setAnalyzeResult] = useState<AnalyzeResult | null>(null);
  const [executeResult, setExecuteResult] = useState<ExecuteResult | null>(null);
  const [whatIfResult, setWhatIfResult] = useState<WhatIfResult | null>(null);
  const [isWhatIfLoading, setIsWhatIfLoading] = useState(false);

  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  function applySeed(s: (typeof SEEDS)[0]) {
    setText(s.text);
    setDomain(s.domain);
    setStep("idle");
    setIngestResult(null);
    setAnalyzeResult(null);
    setExecuteResult(null);
  }

  async function handleIngest() {
    setError("");
    setStep("ingesting");
    try {
      const fd = new FormData();
      fd.append("text", text);
      fd.append("url", url);
      fd.append("csv_data", csv);
      fd.append("domain", domain);
      fd.append("topic", topic);
      fd.append("include_feed", String(includeFeed));
      if (fileRef.current?.files?.[0]) fd.append("file", fileRef.current.files[0]);
      const res = await ingest(fd);
      setIngestResult(res);
      setStep("ingested");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Ingest failed");
      setStep("idle");
    }
  }

  async function handleAnalyze() {
    setError("");
    setStep("analyzing");
    try {
      const res = await analyze(domain);
      setAnalyzeResult(res);
      setStep("analyzed");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Analyze failed");
      setStep("ingested");
    }
  }

  async function handleExecute() {
    setError("");
    setStep("executing");
    try {
      const res = await execute(undefined, domain);
      setExecuteResult(res);
      setStep("done");
      // Auto-save to history
      await historyApi.save({
        domain,
        topic: topic || text.slice(0, 60),
        sources_processed: ingestResult?.sources_processed ?? 0,
        contradictions_found: ingestResult?.contradictions_found ?? 0,
        actions_total: analyzeResult?.action_chain?.length ?? 0,
        total_cost_pkr: res.total_cost_pkr,
        status: "completed",
        ingest_result: ingestResult,
        analyze_result: analyzeResult,
        execute_result: res,
      }).catch(() => {}); // don't fail if not authed
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Execute failed");
      setStep("analyzed");
    }
  }

  async function handleWhatIf(mod: Record<string, unknown>) {
    setWhatIfResult(null);
    setIsWhatIfLoading(true);
    try {
      const res = await whatIf(mod);
      setWhatIfResult(res);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "What-if failed");
    } finally {
      setIsWhatIfLoading(false);
    }
  }

  const metrics = {
    sources: ingestResult?.sources_processed,
    trusted: ingestResult?.sources_trusted,
    contradictions: ingestResult?.contradictions_found,
    actions: analyzeResult?.action_chain?.length,
    cost: executeResult?.total_cost_pkr,
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Navbar metrics={metrics} />
      <div className="flex-1 overflow-auto">
        <div className="grid grid-cols-[280px_1fr_1fr] gap-0 h-full">

          {/* LEFT — Sources */}
          <div className="border-r border-nexus-border overflow-y-auto p-4 flex flex-col gap-4">
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Quick Seeds</p>
              <div className="flex flex-col gap-1.5">
                {SEEDS.map((s) => (
                  <button
                    key={s.label}
                    onClick={() => applySeed(s)}
                    className="text-left px-3 py-2 rounded-lg border border-nexus-border text-xs text-gray-400 hover:border-nexus-cyan/50 hover:text-nexus-cyan transition-all"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Domain</label>
              <select
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                className="mt-1 w-full px-3 py-2 rounded-lg bg-white/5 border border-nexus-border text-sm text-white focus:outline-none focus:ring-2 focus:ring-nexus-cyan/50"
              >
                {DOMAINS.map((d) => <option key={d}>{d}</option>)}
              </select>
            </div>

            <Textarea
              label="Text Source"
              rows={5}
              placeholder="Paste intelligence text, news, reports..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
            <Input label="URL Source" type="url" placeholder="https://..." value={url} onChange={(e) => setUrl(e.target.value)} />
            <Textarea label="CSV Data" rows={3} placeholder="col1,col2&#10;val1,val2" value={csv} onChange={(e) => setCsv(e.target.value)} />

            <div>
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider">PDF Upload</label>
              <input ref={fileRef} type="file" accept=".pdf" className="mt-1 w-full text-xs text-gray-400 file:mr-2 file:py-1 file:px-3 file:rounded file:border file:border-nexus-border file:bg-nexus-card file:text-xs file:text-gray-400 hover:file:border-nexus-cyan" />
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={includeFeed} onChange={(e) => setIncludeFeed(e.target.checked)} className="accent-nexus-cyan" />
              <span className="text-xs text-gray-400">Include live RSS feed</span>
            </label>

            {error && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-xs">
                {error}
              </div>
            )}

            <div className="flex flex-col gap-2 mt-auto pt-2">
              <Button
                onClick={handleIngest}
                loading={step === "ingesting"}
                disabled={!text.trim() && !url.trim() && !csv.trim()}
                className="w-full"
              >
                1. Ingest Sources
              </Button>
              <Button
                variant="outline"
                onClick={handleAnalyze}
                loading={step === "analyzing"}
                disabled={step !== "ingested" && step !== "analyzed"}
                className="w-full"
              >
                2. Run Agents
              </Button>
              <Button
                variant="outline"
                onClick={handleExecute}
                loading={step === "executing"}
                disabled={step !== "analyzed" && step !== "done"}
                className="w-full"
              >
                3. Execute Chain
              </Button>
              {(step === "done" || step === "analyzed") && (
                <Button variant="ghost" size="sm" onClick={() => exportTrace()} className="w-full text-gray-500">
                  Export Trace
                </Button>
              )}
            </div>
          </div>

          {/* CENTER — Agent Debate */}
          <div className="border-r border-nexus-border overflow-y-auto p-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Agent Debate</p>

            {step === "idle" && (
              <div className="flex items-center justify-center h-64 text-gray-600 text-sm">
                Ingest sources to start debate
              </div>
            )}
            {(step === "ingesting" || step === "analyzing") && (
              <div className="flex flex-col items-center gap-3 h-64 justify-center">
                <span className="w-8 h-8 border-2 border-nexus-cyan border-t-transparent rounded-full animate-spin" />
                <p className="text-nexus-cyan text-sm font-mono animate-pulse">
                  {step === "ingesting" ? "Ingesting sources..." : "Agents deliberating..."}
                </p>
              </div>
            )}

            {ingestResult && step !== "analyzing" && step !== "ingesting" && (
              <div className="mb-4 p-3 rounded-lg bg-white/3 border border-nexus-border grid grid-cols-3 gap-3">
                <div className="text-center">
                  <p className="text-lg font-bold text-nexus-cyan font-mono">{ingestResult.sources_processed}</p>
                  <p className="text-[10px] text-gray-500">Sources</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-nexus-green font-mono">{ingestResult.sources_trusted}</p>
                  <p className="text-[10px] text-gray-500">Trusted</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-nexus-amber font-mono">{ingestResult.contradictions_found}</p>
                  <p className="text-[10px] text-gray-500">Conflicts</p>
                </div>
              </div>
            )}

            {analyzeResult && (
              <AgentDebate agents={analyzeResult.agents} resolved={analyzeResult.resolved} />
            )}
          </div>

          {/* RIGHT — Chain + Execution */}
          <div className="overflow-y-auto p-4 flex flex-col gap-4">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Action Chain & Execution</p>

            {analyzeResult && (
              <>
                <ActionChain chain={executeResult?.chain ?? analyzeResult.action_chain} />
                <RiskTimeline chain={executeResult?.chain ?? []} />
              </>
            )}

            {executeResult && (
              <Card className="p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-sm font-semibold text-white">Execution Log</span>
                  <Badge variant="green">
                    {executeResult.failures} failed → {executeResult.recovered} recovered
                  </Badge>
                </div>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {executeResult.log.map((l, i) => (
                    <p
                      key={i}
                      className={`text-xs font-mono leading-relaxed ${l.message.includes("REAL") ? "text-nexus-purple" : "text-gray-500"}`}
                    >
                      <span className="text-gray-700">[{l.time_display}]</span> {l.message}
                    </p>
                  ))}
                </div>
                <div className="mt-3 flex gap-4 text-xs font-mono border-t border-nexus-border pt-3">
                  <span className="text-gray-500">Total: <span className="text-white">PKR {executeResult.total_cost_pkr.toLocaleString()}</span></span>
                  <span className="text-gray-500">Latency: <span className="text-white">{executeResult.total_latency_ms}ms</span></span>
                </div>
              </Card>
            )}

            {/* Learning active badge */}
            {analyzeResult?.learning_active && (
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-nexus-purple/5 border border-nexus-purple/20">
                <span className="w-1.5 h-1.5 rounded-full bg-nexus-purple animate-pulse" />
                <span className="text-xs text-nexus-purple font-mono">
                  Agent learning active — feedback from {(analyzeResult as unknown as { learning_context?: { total_feedback?: number } }).learning_context?.total_feedback} past ratings injected into prompts
                </span>
              </div>
            )}

            {/* Feedback */}
            {step === "done" && executeResult && (
              <FeedbackWidget
                domain={domain}
                agentConfidences={Object.fromEntries(
                  (analyzeResult?.agents ?? []).map((a) => [a.agent, a.confidence])
                )}
              />
            )}

            {/* What-If Panel */}
            {analyzeResult && (
              <Card className="p-4">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">What-If Analysis</p>
                <div className="grid grid-cols-2 gap-2">
                  {WHATIF_PRESETS.map((p) => (
                    <button
                      key={p.label}
                      onClick={() => handleWhatIf(p.mod)}
                      disabled={isWhatIfLoading}
                      className="px-3 py-2 rounded-lg border border-nexus-border text-xs text-gray-400 hover:border-nexus-cyan/50 hover:text-nexus-cyan transition-all text-left flex items-center gap-2"
                    >
                      {isWhatIfLoading ? <span className="w-3 h-3 border-2 border-nexus-cyan border-t-transparent rounded-full animate-spin" /> : null}
                      {p.label}
                    </button>
                  ))}
                </div>
                {whatIfResult && (
                  <div className="mt-3 pt-3 border-t border-nexus-border space-y-1 text-xs font-mono">
                    <p className="text-gray-400">Modified actions: <span className="text-nexus-amber">{whatIfResult.actions_modified}</span></p>
                    <p className="text-gray-400">Cost delta: <span className={whatIfResult.cost_delta_pkr > 0 ? "text-nexus-red" : "text-nexus-green"}>PKR {whatIfResult.cost_delta_pkr > 0 ? "+" : ""}{whatIfResult.cost_delta_pkr.toLocaleString()}</span></p>
                    <p className="text-gray-400">{whatIfResult.feasibility_summary}</p>
                  </div>
                )}
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
