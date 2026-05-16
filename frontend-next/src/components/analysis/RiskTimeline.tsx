import type { ActionItem } from "@/types";

export default function RiskTimeline({ chain }: { chain: ActionItem[] }) {
  const W = 460;
  const H = 120;
  const PAD = { t: 16, r: 16, b: 28, l: 36 };
  const chartW = W - PAD.l - PAD.r;
  const chartH = H - PAD.t - PAD.b;

  const completedSteps = chain.filter((a) => a.status === "DONE" || a.status === "RECOVERED").length;
  const totalSteps = chain.length || 5;

  const points: [number, number][] = [[0, 85]];
  for (let i = 1; i <= totalSteps; i++) {
    const t = (i / totalSteps) * 72;
    const done = i <= completedSteps;
    const risk = 85 - (done ? i * 14 : (completedSteps / totalSteps) * i * 14 * 0.4);
    points.push([t, Math.max(5, risk)]);
  }

  const toX = (t: number) => PAD.l + (t / 72) * chartW;
  const toY = (r: number) => PAD.t + chartH - (r / 100) * chartH;

  const path = points.map(([t, r], i) => `${i === 0 ? "M" : "L"} ${toX(t)} ${toY(r)}`).join(" ");
  const area = path + ` L ${toX(72)} ${PAD.t + chartH} L ${PAD.l} ${PAD.t + chartH} Z`;

  const yTicks = [0, 25, 50, 75, 100];
  const xLabels = ["0h", "18h", "36h", "54h", "72h"];

  return (
    <div>
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Risk Recovery Timeline</p>
      <svg width={W} height={H} className="w-full" viewBox={`0 0 ${W} ${H}`}>
        {/* Grid */}
        {yTicks.map((v) => (
          <g key={v}>
            <line x1={PAD.l} y1={toY(v)} x2={W - PAD.r} y2={toY(v)} stroke="#1a1a2e" strokeWidth="1" />
            <text x={PAD.l - 4} y={toY(v) + 3} fill="#555" fontSize="8" textAnchor="end">{v}</text>
          </g>
        ))}
        {xLabels.map((l, i) => (
          <text key={l} x={toX((i / 4) * 72)} y={H - 4} fill="#555" fontSize="8" textAnchor="middle">{l}</text>
        ))}

        {/* Threshold zones */}
        <rect x={PAD.l} y={toY(100)} width={chartW} height={toY(60) - toY(100)} fill="rgba(239,68,68,0.05)" />
        <rect x={PAD.l} y={toY(60)} width={chartW} height={toY(30) - toY(60)} fill="rgba(245,158,11,0.05)" />
        <rect x={PAD.l} y={toY(30)} width={chartW} height={toY(0) - toY(30)} fill="rgba(0,255,136,0.05)" />

        {/* Area fill */}
        <path d={area} fill="url(#riskGrad)" opacity="0.3" />
        <defs>
          <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ef4444" />
            <stop offset="100%" stopColor="#00ff88" stopOpacity="0.1" />
          </linearGradient>
        </defs>

        {/* Line */}
        <path d={path} fill="none" stroke="#00d4ff" strokeWidth="2" strokeLinecap="round" />

        {/* Points */}
        {points.map(([t, r], i) => (
          <circle
            key={i}
            cx={toX(t)}
            cy={toY(r)}
            r="3"
            fill={i <= completedSteps ? "#00ff88" : "#555"}
            stroke="#0a0a0f"
            strokeWidth="1"
          />
        ))}
      </svg>
    </div>
  );
}
