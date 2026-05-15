# NEXUS — Autonomous Content-to-Action Agent
## Hackathon Challenge 1 Submission

## Project Structure
```
nexus/
├── PLAN.md                     ← Antigravity trace artifact
├── README.md
├── backend/                    ← FastAPI Python backend
│   ├── requirements.txt
│   ├── main.py                 ← 8 REST endpoints + static serve
│   ├── ingestion.py            ← 5-source processor
│   ├── contradiction.py        ← Credibility + conflict + noise
│   ├── constraints.py          ← Budget/time/staff checker
│   ├── agents.py               ← 5 AI agents + ConsensusEngine
│   └── simulator.py            ← Chain execution + failure recovery
├── frontend/
│   └── index.html              ← Single-file React web UI (CDN, no build)
└── nexus_mobile/               ← Flutter APK (4 screens)
    ├── pubspec.yaml
    └── lib/
        ├── main.dart
        ├── config.dart
        ├── models/
        ├── services/
        └── screens/
```

## Architecture overview
5-layer pipeline:
1. **Ingestion Layer** — `ingestion.py`: PDF (PyMuPDF), URL (httpx), CSV (stdlib), text, mock live feed
2. **Intelligence Layer** — `contradiction.py`: credibility scoring, noise filtering, Gemini contradiction + temporal analysis
3. **Agent Layer** — `agents.py`: Orion + Raven + Cipher run via `asyncio.gather` (parallel), then Resolver synthesizes, then Executor plans chain
4. **Simulation Layer** — `simulator.py`: 5-step causal chain, 40% step-3 failure/recovery, before/after state, cost + latency tracking
5. **Presentation Layer** — `frontend/index.html` (web) + Flutter APK (mobile)

## Data source schemas
| Source | Format | Credibility base | Temporal |
|---|---|---|---|
| PDF report | Binary → text | 0.85 | No |
| Text/article | String | 0.65 | No |
| URL fetch | HTML → stripped | 0.70 | No |
| CSV data | Rows → summary | 0.90 | Yes if date column present |
| Mock live feed | Hardcoded string | 0.60 | Yes (timestamp in content) |

## Tools and APIs used
| Tool | Purpose | Version |
|---|---|---|
| FastAPI | Backend REST API | 0.115+ |
| google-generativeai | Gemini 2.0 Flash — all LLM calls | latest |
| PyMuPDF | PDF text extraction | latest |
| httpx | URL fetching with redirect following | latest |
| asyncio.gather | Parallel agent execution | stdlib |
| React 18 | Web UI via CDN — no build step | 18 |
| Flutter | Mobile APK | 3.x |

## How Antigravity is used
- `PLAN.md` is the live Antigravity workplan — updated with ISO timestamps and rationale at each stage
- All 5 agents are orchestrated like Antigravity Manager View tasks: Orion/Raven/Cipher run in parallel, Resolver synthesizes, Executor plans
- `asyncio.gather` maps directly to Antigravity parallel task execution
- `/export-trace` produces `nexus_antigravity_trace.json` containing full agent log, state snapshot, and decision flow
- The web UI shows the Antigravity Agent Orchestration diagram explicitly

## Setup steps
```bash
cd nexus/backend
pip install -r requirements.txt
set GOOGLE_API_KEY=your_key_here   # Windows
# export GOOGLE_API_KEY=your_key_here  (Linux/Mac)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
# Web UI: open http://localhost:8000
# Mobile: cd ../nexus_mobile && flutter pub get && flutter build apk --release
```

## Web UI standout features
- **Antigravity Agent Flow Diagram** — SVG showing the full 5-agent orchestration pipeline with animated data flow
- **SVG Causal Chain Visualization** — animated flowchart with real-time step status (PENDING → RUNNING → DONE / FAILED → RECOVERED)
- **Agent Radar Chart** — SVG polygon chart comparing Orion/Raven/Cipher confidence across 5 dimensions
- **Typewriter Effect** — Agent insights appear character-by-character simulating real AI reasoning
- **⚡ Auto Demo Button** — One-click runs the full Supply Chain scenario end-to-end
- **Live Metrics Bar** — Real-time status, source count, contradiction count, cost in the navbar
- **3-Column Mission Control Layout** — Input | Agents | Execution visible simultaneously

## Robustness scenarios (all triggered by Supply Chain seed)
| Scenario | Trigger | Log message |
|---|---|---|
| URL fetch failure | Blank URL field | `[NEXUS] URL source excluded — fetch failed, credibility scored 0.0` |
| Step 3 chain failure | 40% random | `[NEXUS] Step 3 FAILED — Mock API timeout after 30s. Transaction rolled back.` |
| Low credibility excluded | Score < 0.30 | `[NEXUS] Source excluded: {type} scored {score:.2f} — below minimum threshold 0.30` |
| Contradiction resolved | 2+ conflicting sources | `[NEXUS] Contradiction detected: {A} vs {B} — {reason}. Resolver agent invoked.` |

## Assumptions
1. Gemini 2.0 Flash free tier is sufficient for demo volume
2. All scenario data is fictional and Pakistan-context inspired
3. Step 3 failure is simulated probabilistically — not every run triggers it
4. Constraints are hardcoded defaults; production would load from config
5. In-memory state resets on server restart (by design for demo)

## Privacy note
No real personal data. All scenarios fictional. No data stored persistently.

## Cost and latency
- Cost per Gemini call: ~$0.00 free tier / ~$0.001 paid
- Full pipeline (5 agent calls): ~$0.005
- Average latency: 3–5 seconds end-to-end
- At 10x: asyncio unchanged, add Redis for state
- At 100x: Cloud Run autoscale, BigQuery for state, Pub/Sub for agent coordination

## Demo video script (Supply Chain, 3–5 min)
1. Click **⚡ Auto Demo** OR manually select Logistics + click 🏭 Supply Chain
2. Show **Antigravity Agent Flow** diagram animating
3. Ingest — point to URL failure in log, credibility matrix
4. Show contradiction card (text says "stock fine" vs feed says "critical shortage")
5. Expand investigation path (3 steps)
6. Run Analysis — 3 agent cards typewriter-animate with staggered reveal
7. Show **Agent Radar Chart** — confidence polygon comparison
8. Show Resolver synthesis with 3-step investigation path
9. Show **SVG Causal Chain** — 5 nodes connected by animated arrows
10. Execute Chain — steps light up green, Step 3 flashes red → amber RECOVERED
11. Before/After: amber-highlighted changed fields
12. Click "Compare vs Baseline" — ✓/✗ comparison table
13. Click ↓ Export Trace — download `nexus_antigravity_trace.json`
14. Say: "This file is our Antigravity submission artifact"
