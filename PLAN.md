# NEXUS — Antigravity Agent Build Plan
## Challenge 1: Autonomous Content-to-Action Agent
## Submission deadline: May 20, 2026

## Project Structure
```
nexus/
├── backend/   ← FastAPI + 5 AI modules
├── frontend/  ← React web UI (CDN, no build)
└── nexus_mobile/ ← Flutter APK
```

## Task plan
- [x] PLAN.md — created 2026-05-15T00:00:00Z
- [x] backend/requirements.txt
- [x] backend/ingestion.py — 5-source processor
- [x] backend/contradiction.py — credibility + conflict + noise
- [x] backend/constraints.py — budget/time/staff checker
- [x] backend/agents.py — 5 agents + ConsensusEngine (asyncio.gather)
- [x] backend/simulator.py — chain execution + failure recovery + cost
- [x] backend/main.py — 8 endpoints + static serve from ../frontend
- [x] frontend/index.html — 3-column mission control web UI
- [x] README.md — all required sections
- [x] nexus_mobile/ — Flutter APK 4 screens

## APK Submission Artifact
`nexus_mobile/build/app/outputs/flutter-apk/app-release.apk`

## Run Command
```bash
cd nexus/backend
set GOOGLE_API_KEY=your_key
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Antigravity Reasoning Trace

### 2026-05-15T00:00:00Z — Project scaffolded
Decision: FastAPI for backend, React 18 CDN for web (no build step = easier demo), Flutter for mobile. In-memory state avoids DB overhead for hackathon scope.

### 2026-05-15T00:01:00Z — Ingestion layer complete
5 source types: PDF (fitz.open stream), URL (httpx + HTML strip), CSV (csv.DictReader), text, mock feed. Each returns `credibility_base` for downstream scoring pipeline. Temporal detection via column header keyword matching.

### 2026-05-15T00:02:00Z — Contradiction + Intelligence layer complete
Credibility modifiers: PDF +0.10, CSV +0.05, temporal +0.05, noise terms -0.15, stale terms -0.20. Filter threshold: 0.30. Gemini called once for full contradiction + temporal analysis with structured JSON prompt. Fallback hardcoded for rate-limit resilience.

### 2026-05-15T00:03:00Z — Constraint checker complete
DEFAULT_CONSTRAINTS: PKR 500K budget, 4h response time, 3 staff, medium urgency. Gemini validates each action, returns modified_action if infeasible. Chain validator replaces infeasible actions in-place.

### 2026-05-15T00:04:00Z — 5-agent pipeline complete
**Antigravity parallel execution mapping:**
- Orion (Optimist) + Raven (Pessimist) + Cipher (Realist) → asyncio.gather (parallel, mirrors Antigravity Manager View)
- Weighted confidence: Cipher×0.40 + Orion×0.30 + Raven×0.30
- Resolver synthesizes → ExecutorAgent plans 5-step causal chain
- ConstraintChecker validates entire chain

### 2026-05-15T00:05:00Z — Simulator complete
Step 3 forced failure: `random.random() < 0.40`. Full retry/recovery log sequence. Before-state snapshot before chain, after-state snapshot after. Cost and latency accumulated per step.

### 2026-05-15T00:06:00Z — Backend API complete
8 endpoints: /health /ingest /analyze /execute /state /logs /baseline-comparison /export-trace. Static file mount LAST to avoid route shadowing. CORS open for mobile app.

### 2026-05-15T00:07:00Z — Frontend restructure complete
Moved to frontend/ folder. Backend serves from ../frontend path. 3-column layout: Source Intel | Agent Debate | Chain + Outcome. Standout features:
- Antigravity Agent Flow SVG diagram
- SVG Causal Chain with animated status nodes
- Agent Radar Chart (polygon comparison)
- Typewriter effect for agent insights
- ⚡ Auto Demo button (one-click full scenario)
- Live metrics in nav bar

### 2026-05-15T00:08:00Z — README complete
All required sections: architecture, data schemas, tool table, Antigravity usage, setup, demo script, robustness scenarios, cost/latency, assumptions.

### 2026-05-15T00:09:00Z — Flutter mobile complete
4 screens: InputScreen → DebateScreen → ExecutionScreen → ChainScreen. Seed buttons, animated agent cards, before/after comparison, live log polling, baseline comparison dialog.

## Key Design Decisions
1. **asyncio.gather for agents** — maps exactly to Antigravity parallel task execution model
2. **Gemini 2.0 Flash** — fastest model in Gemini family, reduces perceived latency
3. **In-memory state_store** — acceptable for demo; production would use Redis
4. **Fallback responses** — every Gemini call wrapped in try/except with realistic hardcoded fallback; demo never crashes
5. **Supply Chain seed** — deliberately chosen to trigger ALL 4 robustness scenarios in one flow
6. **SVG visualizations** — no chart library dependency, pure React+SVG, works offline
7. **⚡ Auto Demo** — removes human error from demo execution; judges see the full flow in under 60 seconds
