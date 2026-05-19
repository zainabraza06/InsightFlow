"use client";
import { useEffect, useState } from "react";
import Navbar from "@/components/layout/Navbar";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { adminApi } from "@/lib/api";
import { getUser } from "@/lib/auth";

type Tab = "analytics" | "users" | "history" | "feedback";

export default function AdminPage() {
  const user = getUser();
  const isAdmin = user?.is_admin === true;

  const [activeTab, setActiveTab] = useState<Tab>("analytics");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState("");

  const [stats, setStats] = useState<{
    total_users: number;
    total_runs: number;
    total_feedback: number;
    avg_rating: number;
    total_cost_spent: number;
    domain_stats: Record<string, { runs: number; cost: number }>;
  } | null>(null);

  const [users, setUsers] = useState<Array<{ name: string; email: string; is_admin: boolean }>>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [feedbacks, setFeedbacks] = useState<any[]>([]);

  async function loadData() {
    try {
      setLoading(true);
      const [statsData, usersData, historyData, feedbackData] = await Promise.all([
        adminApi.stats(),
        adminApi.users(),
        adminApi.history(),
        adminApi.feedback(),
      ]);
      setStats(statsData);
      setUsers(usersData);
      setHistory(historyData);
      setFeedbacks(feedbackData);
      setError("");
    } catch (e: any) {
      setError(e.message || "Failed to load admin dashboard data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!isAdmin) return;
    loadData();
  }, [isAdmin]);

  async function handleToggleRole(email: string) {
    if (email.toLowerCase() === user?.email.toLowerCase()) {
      alert("Demoting your own administrative profile is locked to prevent locking out the admin account.");
      return;
    }
    if (!confirm(`Are you sure you want to change privileges/role for operator: ${email}?`)) {
      return;
    }
    try {
      setActionLoading(true);
      await adminApi.toggleRole(email);
      await loadData();
    } catch (e: any) {
      alert(e.message || "Role adjustment transaction failed.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleDeleteHistory(id: string) {
    if (!confirm("Are you sure you want to permanently delete this execution run history? This cannot be undone and will affect global stats.")) {
      return;
    }
    try {
      setActionLoading(true);
      await adminApi.deleteHistory(id);
      await loadData();
    } catch (e: any) {
      alert(e.message || "Telemetry removal transaction failed.");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleResetFeedback() {
    if (!confirm("WARNING: Are you sure you want to permanently clear all customer feedbacks and reset the agent reinforcement learning context? This will recalibrate agent prompt instructions to their default states!")) {
      return;
    }
    try {
      setActionLoading(true);
      await adminApi.resetFeedback();
      await loadData();
      alert("All feedback commentary and reinforcement context has been successfully recalibrated.");
    } catch (e: any) {
      alert(e.message || "Context recalibration failed.");
    } finally {
      setActionLoading(false);
    }
  }

  if (!isAdmin) {
    return (
      <div className="flex flex-col h-screen overflow-hidden">
        <Navbar />
        <div className="flex-1 flex items-center justify-center p-6 bg-nexus-bg">
          <Card className="p-8 max-w-md text-center border-l-4 border-l-nexus-red">
            <span className="text-4xl mb-4 block">🛡️</span>
            <h2 className="text-lg font-bold text-white mb-2">Access Denied</h2>
            <p className="text-sm text-gray-500 mb-6">
              You do not have the required administrative privileges to view the InsightFlow Admin Panel.
            </p>
            <Button onClick={() => window.location.href = "/dashboard"}>
              Return to Dashboard
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-nexus-bg">
      <Navbar />
      <div className="flex-1 overflow-auto p-6">
        <div className="max-w-6xl mx-auto pb-12">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                <span>🛡️</span> Admin Command Center
              </h1>
              <p className="text-sm text-gray-500 mt-1">Platform monitor, execution history, and user feedback metrics</p>
            </div>
            <div className="flex gap-2 bg-nexus-card border border-nexus-border rounded-lg p-1">
              {(["analytics", "users", "history", "feedback"] as Tab[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 rounded-md text-xs font-semibold uppercase tracking-wider transition-all ${
                    activeTab === tab
                      ? "bg-nexus-cyan text-black shadow-md font-bold"
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="p-4 mb-6 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              {error}
            </div>
          )}

          {actionLoading && (
            <div className="p-3 mb-6 rounded-lg bg-nexus-cyan/10 border border-nexus-cyan/30 text-nexus-cyan text-xs font-mono animate-pulse flex items-center gap-2">
              <span className="w-3.5 h-3.5 border-2 border-nexus-cyan border-t-transparent rounded-full animate-spin" />
              Executing administrative database operation...
            </div>
          )}

          {loading ? (
            <div className="flex flex-col items-center justify-center p-24">
              <span className="w-8 h-8 border-4 border-nexus-cyan border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-sm text-gray-400 font-mono">Aggregating platform telemetry...</p>
            </div>
          ) : (
            <>
              {/* Analytics HUD Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <Card className="p-4 border-l-2 border-l-nexus-cyan flex flex-col justify-between h-28">
                  <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Registered Users</p>
                  <div>
                    <h3 className="text-2xl font-bold text-white font-mono">{stats?.total_users || 0}</h3>
                    <p className="text-[10px] text-nexus-cyan mt-1">Active platform profiles</p>
                  </div>
                </Card>

                <Card className="p-4 border-l-2 border-l-nexus-purple flex flex-col justify-between h-28">
                  <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Total Pipeline Executions</p>
                  <div>
                    <h3 className="text-2xl font-bold text-white font-mono">{stats?.total_runs || 0}</h3>
                    <p className="text-[10px] text-nexus-purple mt-1">Completed agent debates</p>
                  </div>
                </Card>

                <Card className="p-4 border-l-2 border-l-nexus-green flex flex-col justify-between h-28">
                  <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Accumulated Budget Spent</p>
                  <div>
                    <h3 className="text-2xl font-bold text-white font-mono">
                      PKR {(stats?.total_cost_spent || 0).toLocaleString()}
                    </h3>
                    <p className="text-[10px] text-nexus-green mt-1">Aggregated action chain costs</p>
                  </div>
                </Card>

                <Card className="p-4 border-l-2 border-l-nexus-amber flex flex-col justify-between h-28">
                  <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Average User Rating</p>
                  <div>
                    <h3 className="text-2xl font-bold text-white font-mono flex items-center gap-1.5">
                      ★ {stats?.avg_rating || 0.0}
                    </h3>
                    <p className="text-[10px] text-nexus-amber mt-1">
                      From {stats?.total_feedback || 0} customer reviews
                    </p>
                  </div>
                </Card>
              </div>

              {/* Tab views */}
              {activeTab === "analytics" && stats && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Domain Breakdown */}
                  <Card className="p-5">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                      <span>📊</span> Domain Execution Breakdown
                    </p>
                    <div className="space-y-4">
                      {Object.keys(stats.domain_stats).length === 0 ? (
                        <p className="text-sm text-gray-500 font-mono text-center py-6">No domain execution statistics recorded.</p>
                      ) : (
                        Object.entries(stats.domain_stats).map(([domain, data]) => {
                          const costShare = stats.total_cost_spent > 0 ? (data.cost / stats.total_cost_spent) * 100 : 0;
                          return (
                            <div key={domain} className="space-y-1 text-xs">
                              <div className="flex justify-between font-mono">
                                <span className="text-white font-semibold">{domain}</span>
                                <span className="text-gray-400">
                                  {data.runs} runs · PKR {data.cost.toLocaleString()}
                                </span>
                              </div>
                              <div className="w-full bg-black/40 h-2 rounded overflow-hidden border border-nexus-border">
                                <div
                                  className="bg-nexus-cyan h-full transition-all duration-500"
                                  style={{ width: `${costShare}%` }}
                                />
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                  </Card>

                  {/* System Environment */}
                  <Card className="p-5 font-mono text-xs space-y-3">
                    <p className="text-xs font-sans font-semibold text-gray-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                      <span>🛡️</span> Command Center Telemetry
                    </p>
                    <div className="flex justify-between border-b border-nexus-border/50 pb-2">
                      <span className="text-gray-500">Security Layer</span>
                      <span className="text-nexus-cyan font-bold">SHA-256 HMAC (JWT)</span>
                    </div>
                    <div className="flex justify-between border-b border-nexus-border/50 pb-2">
                      <span className="text-gray-500">State Persistence</span>
                      <span className="text-nexus-purple">Local Flat-Files</span>
                    </div>
                    <div className="flex justify-between border-b border-nexus-border/50 pb-2">
                      <span className="text-gray-500">Orchestrator Mirror</span>
                      <span className="text-white">Google Antigravity Workplan Schema</span>
                    </div>
                    <div className="flex justify-between border-b border-nexus-border/50 pb-2">
                      <span className="text-gray-500">Agent Framework</span>
                      <span className="text-nexus-green">Google Agent Development Kit (ADK)</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Spreadsheet Sync</span>
                      <span className="text-nexus-amber">Google Sheets API Row Syncing</span>
                    </div>
                  </Card>
                </div>
              )}

              {activeTab === "users" && (
                <Card className="p-4 overflow-hidden border border-nexus-border">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs font-mono">
                      <thead>
                        <tr className="border-b border-nexus-border text-gray-500">
                          <th className="py-3 px-4 font-semibold uppercase">Name</th>
                          <th className="py-3 px-4 font-semibold uppercase">Email Address</th>
                          <th className="py-3 px-4 font-semibold uppercase">Privileges</th>
                          <th className="py-3 px-4 font-semibold uppercase text-center">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-nexus-border/30">
                        {users.map((u) => (
                          <tr key={u.email} className="hover:bg-white/3 transition-colors">
                            <td className="py-3 px-4 text-white font-semibold font-sans">{u.name}</td>
                            <td className="py-3 px-4 text-gray-400">{u.email}</td>
                            <td className="py-3 px-4">
                              {u.is_admin ? (
                                <Badge variant="cyan">Admin Partner</Badge>
                              ) : (
                                <Badge variant="gray">Platform User</Badge>
                              )}
                            </td>
                            <td className="py-2 px-4 text-center">
                              {u.email.toLowerCase() !== user?.email.toLowerCase() ? (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleToggleRole(u.email)}
                                  className="text-[10px] font-semibold border-nexus-border hover:bg-nexus-cyan hover:text-black transition-all"
                                >
                                  Toggle Privileges
                                </Button>
                              ) : (
                                <span className="text-[10px] text-gray-600 italic">Active Self Profile</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}

              {activeTab === "history" && (
                <Card className="p-4 overflow-hidden border border-nexus-border">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs font-mono">
                      <thead>
                        <tr className="border-b border-nexus-border text-gray-500">
                          <th className="py-3 px-4 font-semibold uppercase">Timestamp</th>
                          <th className="py-3 px-4 font-semibold uppercase">Operator</th>
                          <th className="py-3 px-4 font-semibold uppercase">Domain</th>
                          <th className="py-3 px-4 font-semibold uppercase">Topic</th>
                          <th className="py-3 px-4 font-semibold uppercase text-right">Contradictions</th>
                          <th className="py-3 px-4 font-semibold uppercase text-right">Actions Done</th>
                          <th className="py-3 px-4 font-semibold uppercase text-right">Cost</th>
                          <th className="py-3 px-4 font-semibold uppercase text-center">Status</th>
                          <th className="py-3 px-4 font-semibold uppercase text-center">Admin action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-nexus-border/30">
                        {history.length === 0 ? (
                          <tr>
                            <td colSpan={9} className="py-8 text-center text-gray-500">
                              No execution logs recorded.
                            </td>
                          </tr>
                        ) : (
                          history.map((h) => (
                            <tr key={h.id} className="hover:bg-white/3 transition-colors">
                              <td className="py-3 px-4 text-gray-400 whitespace-nowrap">
                                {new Date(h.timestamp).toLocaleString()}
                              </td>
                              <td className="py-3 px-4 text-white font-sans">{h.user_email}</td>
                              <td className="py-3 px-4 text-nexus-cyan font-bold">{h.domain}</td>
                              <td className="py-3 px-4 text-gray-300 truncate max-w-xs">{h.topic}</td>
                              <td className="py-3 px-4 text-right text-nexus-amber font-bold">{h.contradictions_found}</td>
                              <td className="py-3 px-4 text-right text-white font-bold">{h.actions_total}</td>
                              <td className="py-3 px-4 text-right text-nexus-green font-bold">
                                PKR {h.total_cost_pkr.toLocaleString()}
                              </td>
                              <td className="py-3 px-4 text-center">
                                <Badge variant={h.status === "completed" ? "green" : "amber"}>
                                  {h.status}
                                </Badge>
                              </td>
                              <td className="py-2 px-4 text-center">
                                <button
                                  onClick={() => handleDeleteHistory(h.id)}
                                  className="px-2 py-1 text-[10px] font-semibold text-red-400 hover:text-white bg-red-500/10 hover:bg-red-500/30 rounded border border-red-500/20 transition-all font-mono"
                                >
                                  Delete
                                </button>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </Card>
              )}

              {activeTab === "feedback" && (
                <div className="space-y-6">
                  {/* Operations Box */}
                  <Card className="p-5 border-l-4 border-l-nexus-amber flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-white mb-1">Feedback Tuning Operations</h4>
                      <p className="text-xs text-gray-500 max-w-lg">
                        Permanently clear reinforcement comments. Recalibrates active agent prompt instruction contexts to base settings.
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      onClick={handleResetFeedback}
                      className="text-xs font-semibold text-nexus-amber border-nexus-amber/30 hover:bg-nexus-amber hover:text-black transition-all whitespace-nowrap"
                    >
                      Wipe Feedback & Recalibrate agents
                    </Button>
                  </Card>

                  {/* Feedback Table */}
                  <Card className="p-4 overflow-hidden border border-nexus-border">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs font-mono">
                        <thead>
                          <tr className="border-b border-nexus-border text-gray-500">
                            <th className="py-3 px-4 font-semibold uppercase">Timestamp</th>
                            <th className="py-3 px-4 font-semibold uppercase">Operator</th>
                            <th className="py-3 px-4 font-semibold uppercase">Domain</th>
                            <th className="py-3 px-4 font-semibold uppercase text-center">Rating</th>
                            <th className="py-3 px-4 font-semibold uppercase">User Commentary</th>
                            <th className="py-3 px-4 font-semibold uppercase">Agent Configs</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-nexus-border/30">
                          {feedbacks.length === 0 ? (
                            <tr>
                              <td colSpan={6} className="py-8 text-center text-gray-500">
                                No customer review commentary recorded.
                              </td>
                            </tr>
                          ) : (
                            feedbacks.map((f) => (
                              <tr key={f.id} className="hover:bg-white/3 transition-colors">
                                <td className="py-3 px-4 text-gray-400 whitespace-nowrap">
                                  {new Date(f.timestamp).toLocaleString()}
                                </td>
                                <td className="py-3 px-4 text-white font-sans">{f.user_email}</td>
                                <td className="py-3 px-4 text-nexus-cyan font-bold">{f.domain}</td>
                                <td className="py-3 px-4 text-center">
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                    f.rating >= 4 ? "bg-nexus-green/10 text-nexus-green border border-nexus-green/30" :
                                    f.rating <= 2 ? "bg-nexus-red/10 text-nexus-red border border-nexus-red/30" :
                                    "bg-nexus-amber/10 text-nexus-amber border border-nexus-amber/30"
                                  }`}>
                                    ★ {f.rating}
                                  </span>
                                </td>
                                <td className="py-3 px-4 text-gray-300 font-sans max-w-sm italic">
                                  &ldquo;{f.comment || "No commentary left."}&rdquo;
                                </td>
                                <td className="py-3 px-4">
                                  <div className="flex gap-1 flex-wrap">
                                    {Object.entries(f.agent_confidences || {}).map(([agent, conf]) => (
                                      <span key={agent} className="text-[9px] px-1 bg-black/30 border border-nexus-border text-gray-400 rounded">
                                        {agent}: {conf as any}%
                                      </span>
                                    ))}
                                  </div>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </Card>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
