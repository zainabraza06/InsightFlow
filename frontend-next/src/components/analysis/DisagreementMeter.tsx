import { clsx } from "clsx";
import type { AgentResult } from "@/types";

export default function DisagreementMeter({ agents }: { agents: AgentResult[] }) {
  if (!agents?.length) return null;

  const confidences = agents.map((a) => a.confidence);
  const max = Math.max(...confidences);
  const min = Math.min(...confidences);
  const spread = max - min;

  const level = spread > 30 ? "red" : spread > 15 ? "amber" : "green";
  const label = spread > 30 ? "High Conflict" : spread > 15 ? "Moderate Debate" : "Strong Consensus";

  return (
    <div className="p-3 rounded-lg bg-white/3 border border-nexus-border">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Agent Disagreement</span>
        <span
          className={clsx("text-xs font-bold px-2 py-0.5 rounded-full", {
            "text-nexus-green bg-nexus-green/10": level === "green",
            "text-nexus-amber bg-nexus-amber/10": level === "amber",
            "text-nexus-red bg-nexus-red/10": level === "red",
          })}
        >
          {label}
        </span>
      </div>
      <div className="space-y-1.5">
        {agents.map((a) => (
          <div key={a.agent} className="flex items-center gap-2">
            <span className="w-14 text-[10px] text-gray-500 font-mono">{a.agent}</span>
            <div className="flex-1 h-1.5 bg-nexus-border rounded-full overflow-hidden">
              <div
                className={clsx("h-full rounded-full transition-all duration-700", {
                  "bg-nexus-cyan": a.agent === "Cipher",
                  "bg-nexus-green": a.agent === "Orion",
                  "bg-nexus-red": a.agent === "Raven",
                  "bg-nexus-purple": a.agent === "Resolver",
                })}
                style={{ width: `${a.confidence}%` }}
              />
            </div>
            <span className="w-8 text-right text-[10px] text-gray-400 font-mono">{a.confidence}%</span>
          </div>
        ))}
      </div>
      {spread > 20 && (
        <p className="mt-2 text-[10px] text-nexus-amber">
          ⚠ Spread {spread}pts — Resolver weighted synthesis applied
        </p>
      )}
    </div>
  );
}
