"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/layout/Navbar";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import { historyApi } from "@/lib/api";
import type { HistoryEntry } from "@/types";

export default function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    historyApi.list()
      .then(setEntries)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Failed to load history"))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(id: string) {
    setDeleting(id);
    try {
      await historyApi.delete(id);
      setEntries((prev) => prev.filter((e) => e.id !== id));
    } catch {
      setError("Failed to delete entry");
    } finally {
      setDeleting(null);
    }
  }

  const domainColor: Record<string, "cyan" | "purple" | "green" | "amber"> = {
    "Healthcare": "red" as unknown as "amber",
    "Supply Chain": "cyan",
    "Agriculture": "green",
    "Business": "purple",
    "Finance": "amber",
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Navbar />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-xl font-bold text-white">Analysis History</h1>
              <p className="text-sm text-gray-500 mt-1">Your past InsightFlow analyses, saved automatically after execution</p>
            </div>
            <Link href="/analyze">
              <Button>New Analysis</Button>
            </Link>
          </div>

          {loading && (
            <div className="flex justify-center py-20">
              <LoadingSpinner size="lg" />
            </div>
          )}

          {error && (
            <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              {error}
            </div>
          )}

          {!loading && !error && entries.length === 0 && (
            <div className="text-center py-20">
              <p className="text-4xl mb-4">📋</p>
              <p className="text-gray-400 text-sm">No analyses yet.</p>
              <p className="text-gray-600 text-xs mt-2">Run an analysis from the Dashboard — it saves automatically after execution.</p>
            </div>
          )}

          <div className="grid gap-4">
            {entries.map((entry) => (
              <Card key={entry.id} className="p-5 hover:border-nexus-cyan/30 transition-all group">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <Badge variant={domainColor[entry.domain] ?? "gray"}>{entry.domain}</Badge>
                      <Badge variant={entry.status === "completed" ? "green" : "amber"}>{entry.status}</Badge>
                      <span className="text-xs text-gray-600 font-mono ml-auto">
                        {new Date(entry.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-white font-medium truncate">{entry.topic || "Untitled analysis"}</p>
                    <div className="flex items-center gap-4 mt-3 text-xs font-mono text-gray-500">
                      <span>Sources: <span className="text-gray-300">{entry.sources_processed}</span></span>
                      <span>Conflicts: <span className="text-nexus-amber">{entry.contradictions_found}</span></span>
                      <span>Actions: <span className="text-nexus-purple">{entry.actions_total}</span></span>
                      <span>Cost: <span className="text-white">PKR {entry.total_cost_pkr.toLocaleString()}</span></span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Link href={`/history/${entry.id}`}>
                      <Button variant="outline" size="sm">View</Button>
                    </Link>
                    <Button
                      variant="danger"
                      size="sm"
                      loading={deleting === entry.id}
                      onClick={() => handleDelete(entry.id)}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
