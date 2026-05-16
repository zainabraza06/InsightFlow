"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Navbar from "@/components/layout/Navbar";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import AgentDebate from "@/components/analysis/AgentDebate";
import ActionChain from "@/components/analysis/ActionChain";
import RiskTimeline from "@/components/analysis/RiskTimeline";
import FeedbackWidget from "@/components/analysis/FeedbackWidget";
import { historyApi } from "@/lib/api";
import type { HistoryDetail } from "@/types";

export default function HistoryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [entry, setEntry] = useState<HistoryDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    historyApi.get(id)
      .then(setEntry)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Not found"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="flex-1 flex justify-center items-center py-20"><LoadingSpinner size="lg" /></div>;
  if (error || !entry) return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4">
      <p className="text-red-400">{error || "Not found"}</p>
      <Link href="/history"><Button variant="outline">Back to History</Button></Link>
    </div>
  );

  const chain = entry.execute_result?.chain ?? entry.analyze_result?.action_chain ?? [];

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Navbar />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-4 mb-6">
            <Link href="/history">
              <Button variant="ghost" size="sm">← Back</Button>
            </Link>
            <div>
              <h1 className="text-lg font-bold text-white">{entry.topic || "Analysis Detail"}</h1>
              <p className="text-xs text-gray-500 font-mono mt-0.5">{new Date(entry.timestamp).toLocaleString()} · {entry.domain}</p>
            </div>
            <div className="ml-auto flex gap-2">
              <Badge variant="green">{entry.status}</Badge>
            </div>
          </div>

          {/* Summary row */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            {[
              { label: "Sources", value: entry.sources_processed, color: "text-nexus-cyan" },
              { label: "Contradictions", value: entry.contradictions_found, color: "text-nexus-amber" },
              { label: "Actions", value: entry.actions_total, color: "text-nexus-purple" },
              { label: "Total Cost", value: `PKR ${entry.total_cost_pkr.toLocaleString()}`, color: "text-white" },
            ].map((s) => (
              <Card key={s.label} className="p-4 text-center">
                <p className={`text-2xl font-bold font-mono ${s.color}`}>{s.value}</p>
                <p className="text-xs text-gray-500 mt-1">{s.label}</p>
              </Card>
            ))}
          </div>

          <div className="mb-4">
            <FeedbackWidget
              domain={entry.domain}
              analysisId={entry.id}
            />
          </div>

          <div className="grid grid-cols-[1fr_1fr] gap-6">
            {/* Agent Debate */}
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Agent Debate</p>
              {entry.analyze_result ? (
                <AgentDebate agents={entry.analyze_result.agents} resolved={entry.analyze_result.resolved} />
              ) : (
                <Card className="p-6 text-center text-gray-600 text-sm">No agent data</Card>
              )}
            </div>

            {/* Action Chain */}
            <div className="flex flex-col gap-4">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Action Chain</p>
                <ActionChain chain={chain} />
              </div>
              {chain.length > 0 && <RiskTimeline chain={chain} />}
              {entry.execute_result && (
                <Card className="p-4">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Execution Summary</p>
                  <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                    <div>
                      <span className="text-gray-500">Failures: </span>
                      <span className="text-nexus-red">{entry.execute_result.failures}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Recovered: </span>
                      <span className="text-nexus-green">{entry.execute_result.recovered}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Latency: </span>
                      <span className="text-white">{entry.execute_result.total_latency_ms}ms</span>
                    </div>
                    <div>
                      <span className="text-gray-500">Cost: </span>
                      <span className="text-white">PKR {entry.execute_result.total_cost_pkr.toLocaleString()}</span>
                    </div>
                  </div>
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
