import type { AgentResult } from "@/types";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import DisagreementMeter from "./DisagreementMeter";

const AGENT_CONFIG: Record<string, { color: "cyan" | "red" | "green" | "purple"; role: string }> = {
  Orion: { color: "green", role: "Optimist" },
  Raven: { color: "red", role: "Pessimist" },
  Cipher: { color: "cyan", role: "Realist" },
  Resolver: { color: "purple", role: "Synthesizer" },
  Executor: { color: "cyan", role: "Action Planner" },
};

export default function AgentDebate({
  agents,
  resolved,
}: {
  agents: AgentResult[];
  resolved?: { final_insight: string; confidence: number; contradiction_resolution: string };
}) {
  const primary = agents.filter((a) => ["Orion", "Raven", "Cipher", "Executor"].includes(a.agent));
  const resolver = agents.find((a) => a.agent === "Resolver");

  return (
    <div className="flex flex-col gap-4">
      <DisagreementMeter agents={primary} />

      <div className="grid gap-3">
        {primary.map((agent) => {
          const cfg = AGENT_CONFIG[agent.agent] ?? { color: "gray" as const, role: "" };
          return (
            <Card key={agent.agent} glow={cfg.color} className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-sm text-white">{agent.agent}</span>
                  <Badge variant={cfg.color}>{cfg.role}</Badge>
                </div>
                <span className="text-xs font-mono text-gray-400">{agent.confidence}% conf</span>
              </div>
              <p className="text-sm text-gray-300 leading-relaxed">{agent.insight}</p>
              {agent.key_risks && agent.key_risks.length > 0 && (
                <ul className="mt-2 space-y-0.5">
                  {agent.key_risks.slice(0, 2).map((r, i) => (
                    <li key={i} className="text-xs text-gray-500 flex gap-1.5">
                      <span className="text-nexus-amber shrink-0">▸</span> {r}
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          );
        })}
      </div>

      {(resolver || resolved) && (
        <Card glow="purple" className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="font-mono font-bold text-sm text-white">Resolver</span>
            <Badge variant="purple">Synthesis</Badge>
            {resolved && (
              <span className="ml-auto text-xs font-mono text-gray-400">{resolved.confidence}% conf</span>
            )}
          </div>
          <p className="text-sm text-gray-300 leading-relaxed">
            {resolved?.final_insight || resolver?.insight || ""}
          </p>
          {resolved?.contradiction_resolution && (
            <p className="mt-2 text-xs text-nexus-purple/70">{resolved.contradiction_resolution}</p>
          )}
        </Card>
      )}
    </div>
  );
}
