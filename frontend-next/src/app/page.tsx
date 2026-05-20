import Link from "next/link";

const features = [
  { icon: "🔬", title: "Multi-Source Ingestion", desc: "PDF, URL, CSV, text, and live RSS feeds processed simultaneously" },
  { icon: "🤖", title: "5-Agent Consensus", desc: "Orion, Raven, Cipher debate in parallel; Resolver synthesizes truth" },
  { icon: "⚡", title: "Contradiction Detection", desc: "Gemini-powered credibility scoring filters noise automatically" },
  { icon: "🛡️", title: "Constraint Validation", desc: "Budget, time, and staff limits enforced on every action chain" },
  { icon: "🔄", title: "Failure Recovery", desc: "Automatic retry with rollback when integrations fail" },
  { icon: "🔮", title: "What-If Analysis", desc: "Counterfactual constraint simulation with cost delta reporting" },
];

const stats = [
  { value: "5", label: "AI Agents" },
  { value: "3", label: "Real Integrations" },
  { value: "100%", label: "Failure Recovery" },
  { value: "5×", label: "Insight Depth" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-nexus-bg flex flex-col">
      {/* Nav */}
      <nav className="border-b border-nexus-border px-8 py-4 flex items-center justify-between">
        <span className="font-mono font-bold text-nexus-cyan text-xl tracking-widest">InsightFlow</span>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-sm text-gray-400 hover:text-white transition-colors px-4 py-2 rounded-lg">
            Login
          </Link>
          <Link
            href="/register"
            className="text-sm font-semibold bg-nexus-cyan text-black px-4 py-2 rounded-lg hover:bg-cyan-300 transition-colors"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center px-8 py-24 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-nexus-cyan/30 bg-nexus-cyan/5 text-nexus-cyan text-xs font-semibold mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-nexus-cyan animate-pulse" />
          Challenge 1 — Autonomous Content-to-Action Agent
        </div>
        <h1 className="text-5xl md:text-7xl font-bold text-white leading-tight max-w-4xl">
          Intelligence that
          <span className="text-nexus-cyan"> acts</span>
        </h1>
        <p className="mt-6 text-lg text-gray-400 max-w-2xl leading-relaxed">
          InsightFlow ingests any source, runs 5 AI agents in parallel, resolves contradictions, checks constraints, and executes a verified action chain — automatically.
        </p>
        <div className="mt-10 flex items-center gap-4">
          <Link
            href="/register"
            className="font-semibold bg-nexus-cyan text-black px-8 py-3.5 rounded-lg hover:bg-cyan-300 transition-colors text-base"
          >
            Start Analysis
          </Link>
          <Link
            href="/login"
            className="font-semibold border border-nexus-border text-gray-300 px-8 py-3.5 rounded-lg hover:border-nexus-cyan hover:text-nexus-cyan transition-colors text-base"
          >
            Sign In
          </Link>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-nexus-border bg-nexus-card">
        <div className="max-w-5xl mx-auto px-8 py-8 grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <p className="text-3xl font-bold text-nexus-cyan font-mono">{s.value}</p>
              <p className="text-sm text-gray-500 mt-1">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-8 py-20 w-full">
        <h2 className="text-2xl font-bold text-white text-center mb-12">Built for critical decisions</h2>
        <div className="grid md:grid-cols-3 gap-5">
          {features.map((f) => (
            <div key={f.title} className="p-6 rounded-xl border border-nexus-border bg-nexus-card hover:border-nexus-cyan/30 transition-all group">
              <span className="text-3xl mb-4 block">{f.icon}</span>
              <h3 className="font-semibold text-white mb-2 group-hover:text-nexus-cyan transition-colors">{f.title}</h3>
              <p className="text-sm text-gray-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-nexus-border px-8 py-6 text-center">
        <p className="text-sm text-gray-600 font-mono">InsightFlow v2.0 · Antigravity Hackathon Challenge 1</p>
      </footer>
    </div>
  );
}
