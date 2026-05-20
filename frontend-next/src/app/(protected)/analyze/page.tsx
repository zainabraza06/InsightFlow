"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/layout/Navbar";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";
import { Input, Textarea } from "@/components/ui/Input";
import { ingest, analyze, execute, historyApi } from "@/lib/api";
import type { IngestResult, AnalyzeResult, ExecuteResult } from "@/types";

const DOMAINS = ["Business", "Healthcare", "Supply Chain", "Agriculture", "Finance", "Government"];
const STEPS = ["Source Input", "Configure", "Results"];

const DEMO_SEED = {
  topic: "Punjab Wheat Export Ban — Surplus vs Yield Gap",
  domain: "Agriculture",
  text: `Government press release (May 2026): Punjab wheat export ban has been lifted. The Ministry of Food Security confirms a national surplus of 2.4 million metric tons above consumption needs. Export quota set at 1.2 million MT for Q3 2026.

Ground report from District Agriculture Officers (May 2026): Flood damage across southern Punjab reduced yield by 30% below target. Districts of Muzaffargarh, Rajanpur, and DG Khan report critical shortfalls. Field data shows actual production at 18.6 million MT against a 26.5 million MT target. Surplus claim is disputed by district officers.`,
  csvData: `District,Yield_MT,Target_MT,Flood_Affected_Ha,Status
Lahore,850000,900000,12000,On Target
Multan,620000,880000,95000,Below Target
Faisalabad,910000,950000,8500,On Target
Muzaffargarh,340000,780000,185000,Critical Shortage
Rajanpur,290000,720000,210000,Critical Shortage
DG Khan,310000,750000,198000,Critical Shortage
Bahawalpur,480000,820000,132000,Below Target
Rawalpindi,770000,800000,15000,On Target`,
};

export default function AnalyzePage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [domain, setDomain] = useState("Business");
  const [topic, setTopic] = useState("");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [csvData, setCsvData] = useState("");
  const [includeFeed, setIncludeFeed] = useState(false);

  function loadDemo() {
    setTopic(DEMO_SEED.topic);
    setDomain(DEMO_SEED.domain);
    setText(DEMO_SEED.text);
    setCsvData(DEMO_SEED.csvData);
  }
  const [budget, setBudget] = useState("500000");
  const [timeHours, setTimeHours] = useState("4");
  const [staff, setStaff] = useState("3");
  const [urgency, setUrgency] = useState<"low" | "medium" | "high" | "critical">("medium");

  const [ingestResult, setIngestResult] = useState<IngestResult | null>(null);
  const [analyzeResult, setAnalyzeResult] = useState<AnalyzeResult | null>(null);
  const [executeResult, setExecuteResult] = useState<ExecuteResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleNext() {
    if (currentStep === 0) {
      if (!text.trim() && !url.trim()) { setError("Enter at least one source"); return; }
      setError("");
      setLoading(true);
      try {
        const fd = new FormData();
        fd.append("text", text);
        fd.append("url", url);
        fd.append("csv_data", csvData);
        fd.append("domain", domain);
        fd.append("topic", topic);
        fd.append("include_feed", String(includeFeed));
        const res = await ingest(fd);
        setIngestResult(res);
        setCurrentStep(1);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Ingest failed");
      } finally {
        setLoading(false);
      }
    } else if (currentStep === 1) {
      setError("");
      setLoading(true);
      try {
        const constraints = {
          budget_pkr: Number(budget),
          max_response_time_hours: Number(timeHours),
          max_staff: Number(staff),
          urgency,
        };
        const aRes = await analyze(domain, constraints);
        setAnalyzeResult(aRes);
        const eRes = await execute(undefined, domain);
        setExecuteResult(eRes);
        // save to history
        await historyApi.save({
          domain, topic,
          sources_processed: ingestResult?.sources_processed ?? 0,
          contradictions_found: ingestResult?.contradictions_found ?? 0,
          actions_total: aRes.action_chain?.length ?? 0,
          total_cost_pkr: eRes.total_cost_pkr,
          status: "completed",
          ingest_result: ingestResult,
          analyze_result: aRes,
          execute_result: eRes,
        }).catch(() => {});
        setCurrentStep(2);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Analysis failed");
      } finally {
        setLoading(false);
      }
    }
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Navbar />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-2xl mx-auto">
          <div className="mb-8">
            <h1 className="text-xl font-bold text-white mb-4">New Analysis</h1>
            {/* Step indicator */}
            <div className="flex items-center gap-0">
              {STEPS.map((s, i) => (
                <div key={s} className="flex items-center flex-1">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all ${i <= currentStep ? "bg-nexus-cyan text-black" : "bg-nexus-border text-gray-600"}`}>
                    {i < currentStep ? "✓" : i + 1}
                  </div>
                  <span className={`ml-2 text-xs ${i === currentStep ? "text-nexus-cyan font-semibold" : "text-gray-600"}`}>{s}</span>
                  {i < STEPS.length - 1 && <div className={`flex-1 h-px mx-3 ${i < currentStep ? "bg-nexus-cyan" : "bg-nexus-border"}`} />}
                </div>
              ))}
            </div>
          </div>

          {currentStep === 0 && (
            <Card className="p-6 space-y-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-white">Add your sources</h2>
                <button onClick={loadDemo} className="text-xs text-nexus-cyan hover:text-nexus-cyan/70 font-mono transition-colors">
                  Load demo data ↗
                </button>
              </div>
              <Input label="Analysis Topic" placeholder="e.g. Supply chain disruption in Karachi" value={topic} onChange={(e) => setTopic(e.target.value)} />
              <div>
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Domain</label>
                <select value={domain} onChange={(e) => setDomain(e.target.value)}
                  className="mt-1 w-full px-3 py-2 rounded-lg bg-white/5 border border-nexus-border text-sm text-white focus:outline-none focus:ring-2 focus:ring-nexus-cyan/50">
                  {DOMAINS.map((d) => <option key={d}>{d}</option>)}
                </select>
              </div>
              <Textarea label="Text Source" rows={6} placeholder="Paste intelligence reports, news, data..." value={text} onChange={(e) => setText(e.target.value)} />
              <Textarea label="CSV Data" rows={4} placeholder={"District,Yield_MT,Target_MT\nLahore,850000,900000"} value={csvData} onChange={(e) => setCsvData(e.target.value)} />
              <Input label="URL Source" type="url" placeholder="https://..." value={url} onChange={(e) => setUrl(e.target.value)} />
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={includeFeed} onChange={(e) => setIncludeFeed(e.target.checked)} className="accent-nexus-cyan" />
                <span className="text-sm text-gray-400">Include live RSS feed for this domain</span>
              </label>
              {error && <p className="text-xs text-red-400">{error}</p>}
              <Button onClick={handleNext} loading={loading} className="w-full" size="lg">
                Ingest & Continue
              </Button>
            </Card>
          )}

          {currentStep === 1 && ingestResult && (
            <Card className="p-6 space-y-5">
              <div className="grid grid-cols-3 gap-4 p-4 rounded-lg bg-white/3 border border-nexus-border">
                <div className="text-center"><p className="text-xl font-bold text-nexus-cyan font-mono">{ingestResult.sources_processed}</p><p className="text-xs text-gray-500">Sources</p></div>
                <div className="text-center"><p className="text-xl font-bold text-nexus-green font-mono">{ingestResult.sources_trusted}</p><p className="text-xs text-gray-500">Trusted</p></div>
                <div className="text-center">
                  <p className="text-xl font-bold text-nexus-amber font-mono">{ingestResult.contradictions_found}</p>
                  <p className="text-xs text-gray-500">Conflicts</p>
                  {ingestResult.contradictions_found > 0 && (
                    <p className="text-[10px] text-gray-600 mt-0.5 font-mono">
                      {ingestResult.internal_contradictions_found
                        ? `${ingestResult.internal_contradictions_found} internal`
                        : null}
                      {ingestResult.internal_contradictions_found && ingestResult.cross_source_contradictions_found
                        ? " · "
                        : null}
                      {ingestResult.cross_source_contradictions_found
                        ? `${ingestResult.cross_source_contradictions_found} cross-src`
                        : null}
                    </p>
                  )}
                </div>
              </div>
              <h2 className="text-sm font-semibold text-white">Configure constraints</h2>
              <Input label="Budget (PKR)" type="number" value={budget} onChange={(e) => setBudget(e.target.value)} />
              <Input label="Max Response Time (hours)" type="number" value={timeHours} onChange={(e) => setTimeHours(e.target.value)} />
              <Input label="Max Staff" type="number" value={staff} onChange={(e) => setStaff(e.target.value)} />
              <div>
                <label className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Urgency</label>
                <select value={urgency} onChange={(e) => setUrgency(e.target.value as "low" | "medium" | "high" | "critical")}
                  className="mt-1 w-full px-3 py-2 rounded-lg bg-white/5 border border-nexus-border text-sm text-white focus:outline-none focus:ring-2 focus:ring-nexus-cyan/50">
                  {["low", "medium", "high", "critical"].map((u) => <option key={u}>{u}</option>)}
                </select>
              </div>
              {error && <p className="text-xs text-red-400">{error}</p>}
              <Button onClick={handleNext} loading={loading} className="w-full" size="lg">
                {loading ? "Running 5 agents..." : "Run Analysis & Execute"}
              </Button>
            </Card>
          )}

          {currentStep === 2 && analyzeResult && executeResult && (
            <Card className="p-6 space-y-4">
              <div className="flex items-center gap-3">
                <span className="text-2xl">✅</span>
                <div>
                  <h2 className="text-sm font-semibold text-white">Analysis Complete</h2>
                  <p className="text-xs text-gray-500">Saved to history automatically</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-white/3 border border-nexus-border text-center">
                  <p className="text-xl font-bold text-nexus-cyan font-mono">{analyzeResult.consensus_confidence}%</p>
                  <p className="text-xs text-gray-500">Consensus Confidence</p>
                </div>
                <div className="p-3 rounded-lg bg-white/3 border border-nexus-border text-center">
                  <p className="text-xl font-bold text-white font-mono">PKR {executeResult.total_cost_pkr.toLocaleString()}</p>
                  <p className="text-xs text-gray-500">Total Cost</p>
                </div>
              </div>
              <p className="text-sm text-gray-300 leading-relaxed">{analyzeResult.resolved?.final_insight}</p>
              <div className="flex gap-3">
                <Button onClick={() => router.push("/history")} className="flex-1">View in History</Button>
                <Button variant="outline" onClick={() => { setCurrentStep(0); setIngestResult(null); setAnalyzeResult(null); setExecuteResult(null); }} className="flex-1">
                  New Analysis
                </Button>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
