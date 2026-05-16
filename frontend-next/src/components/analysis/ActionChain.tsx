import type { ActionItem } from "@/types";
import Badge from "@/components/ui/Badge";
import { clsx } from "clsx";

export default function ActionChain({ chain }: { chain: ActionItem[] }) {
  if (!chain?.length) return null;

  return (
    <div className="space-y-2">
      {chain.map((action, idx) => (
        <div
          key={idx}
          className={clsx(
            "p-3 rounded-lg border transition-all",
            action.status === "DONE" || action.status === "RECOVERED"
              ? "border-nexus-green/30 bg-nexus-green/5"
              : action.status === "FAILED"
              ? "border-nexus-red/30 bg-nexus-red/5"
              : "border-nexus-border bg-nexus-card"
          )}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2 flex-1 min-w-0">
              <span
                className={clsx(
                  "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5",
                  action.status === "DONE" ? "bg-nexus-green text-black" :
                  action.status === "RECOVERED" ? "bg-nexus-amber text-black" :
                  action.status === "FAILED" ? "bg-nexus-red text-white" :
                  "bg-nexus-cyan/20 text-nexus-cyan"
                )}
              >
                {action.step}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-white font-medium leading-snug">{action.action}</p>
                <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{action.rationale}</p>
              </div>
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              {action.status && (
                <Badge
                  variant={
                    action.status === "DONE" ? "green" :
                    action.status === "RECOVERED" ? "amber" :
                    action.status === "FAILED" ? "red" : "gray"
                  }
                >
                  {action.status}
                </Badge>
              )}
              {action.real_result && (action.real_result as { real?: boolean }).real && (
                <Badge variant="purple">REAL</Badge>
              )}
            </div>
          </div>
          <div className="mt-2 flex items-center gap-3 text-[10px] text-gray-500 font-mono">
            <span>PKR {action.estimated_cost_pkr?.toLocaleString()}</span>
            <span>·</span>
            <span>{action.estimated_time_minutes}min</span>
            {action.was_modified && (
              <>
                <span>·</span>
                <span className="text-nexus-amber">⚠ constraint-modified</span>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
