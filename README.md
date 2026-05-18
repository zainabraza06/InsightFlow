# NEXUS — Autonomous Content-to-Action Agent
## Hackathon Challenge 1 Submission

---

## Project Structure

```
nexus/
├── PLAN.md                          ← Antigravity workplan + reasoning trace
├── README.md
├── backend/                         ← FastAPI Python backend (port 8000)
│   ├── requirements.txt
│   ├── main.py                      ← 10 REST endpoints
│   ├── ingestion.py                 ← 5-source processor (PDF/URL/CSV/text/feed)
│   ├── contradiction.py             ← Credibility scoring + conflict detection
│   ├── constraints.py               ← Budget / time / staff checker
│   ├── agents.py                    ← 5 AI agents + ConsensusEngine (custom flow)
│   ├── sdk_agents.py                ← SDKConsensusEngine (google-genai native flow)
│   ├── simulator.py                 ← Chain execution + failure recovery
│   ├── real_actions.py              ← Real email / Google Sheets / Slack webhook
│   ├── auth.py                      ← JWT register / login
│   ├── history_store.py             ← Per-user analysis history
│   ├── feedback_store.py            ← Agent learning from user ratings
│   └── test_challenge1.py           ← 80-test Challenge 1 requirement suite
├── frontend-next/                   ← Next.js 14 web app (port 3000)
│   ├── src/app/                     ← App Router pages
│   │   ├── (auth)/login             ← Login page
│   │   ├── (auth)/register          ← Register page
│   │   └── (protected)/
│   │       ├── dashboard/           ← Main pipeline UI
│   │       ├── analyze/             ← Analysis results
│   │       ├── history/             ← Past analyses
│   │       ├── trace/               ← Agent execution trace viewer
│   │       └── settings/            ← User settings
│   └── src/components/analysis/
│       ├── AgentDebate.tsx          ← Orion / Raven / Cipher cards
│       ├── ActionChain.tsx          ← 5-step causal chain
│       ├── DisagreementMeter.tsx    ← Agent confidence divergence
│       └── RiskTimeline.tsx         ← Temporal risk visualization
└── nexus_mobile/                    ← Flutter mobile app (Android APK)
    ├── pubspec.yaml
    └── lib/
        ├── main.dart
        ├── config.dart              ← Backend URL config
        └── screens/
            ├── login_screen.dart
            ├── register_screen.dart
            ├── input_screen.dart    ← Source ingestion
            ├── debate_screen.dart   ← Agent analysis
            ├── chain_screen.dart    ← Action chain
            ├── execution_screen.dart← Simulation results
            ├── history_screen.dart
            └── settings_screen.dart
```

---

## Architecture Overview

5-layer pipeline: **Input → Intelligence → Agents → Simulation → Outcome**

```
[Sources: text / CSV / PDF / URL / feed]
        ↓
  IngestionEngine          credibility_base per source type
        ↓
  ContradictionEngine      score, filter noise, detect conflicts, temporal trend
        ↓
  ┌─────────────────────────────────┐
  │  Orion (Optimist)  asyncio      │
  │  Raven  (Pessimist) .gather()   │  ← parallel, mirrors Antigravity Manager View
  │  Cipher (Realist)               │
  └───────────────┬─────────────────┘
                  ↓
           ResolverAgent       synthesizes 3 perspectives into final insight
                  ↓
           ExecutorAgent       plans 5-step causal action chain (validate_action tool)
                  ↓
         ConstraintChecker     flags over-budget / over-time / over-staff actions
                  ↓
         ActionSimulator       executes chain: email + Sheets + Slack + failure recovery
                  ↓
  [Before/After state · Execution log · /export-trace artifact]
```

Two execution flows selectable via `POST /analyze { "flow_type": "custom" | "google_sdk" }`:
- **custom** — ADK-backed `ConsensusEngine` with OpenRouter → Gemini fallback chain
- **google_sdk** — `SDKConsensusEngine` using `google-genai` native function calling

---

## Data Source Credibility

| Source | Format | Base score | Modifier |
|---|---|---|---|
| CSV report | Rows → summary | 0.90 | +0.05 if date column present |
| PDF document | Binary → text | 0.85 | +0.10 type bonus |
| URL fetch | HTML → stripped | 0.70 | −0.20 if stale terms |
| Text / article | String | 0.65 | −0.15 if noise terms (rumor, breaking) |
| Mock live feed | Hardcoded string | 0.60 | — |
| Failed source | Any | 0.00 | Excluded automatically |

Threshold: sources below **0.30** are excluded before agents run.

---

## Tools and APIs

| Tool / API | Purpose |
|---|---|
| **FastAPI** | Backend REST API |
| **google-genai** | Gemini 2.5 Flash Lite — all LLM calls (contradiction detection, 5 agents) |
| **google-genai native tools** | SDK-native function calling for `validate_action` in Executor |
| **PyMuPDF** | PDF text extraction |
| **httpx** | Async HTTP — URL fetching + OpenRouter calls |
| **asyncio.gather** | Parallel Orion / Raven / Cipher execution |
| **gspread + google-auth** | Real Google Sheets dashboard update (Step 3) |
| **smtplib** | Real HTML stakeholder email (Step 2) |
| **Slack webhook** | Real Slack mitigation alert (Step 4) |
| **Next.js 14** | Web frontend (App Router) |
| **Flutter** | Mobile APK (Android) |
| **JWT / pyjwt** | Auth tokens |

---

## How Google Antigravity Is Used

- `PLAN.md` is the live Antigravity workplan — ISO-timestamped decisions and rationale at each stage
- All 5 agents are orchestrated like Antigravity Manager View tasks:
  - **Orion + Raven + Cipher** run via `asyncio.gather` (parallel execution, mirrors Antigravity parallel task model)
  - **Resolver** synthesizes — sequential dependency, like an Antigravity blocking task
  - **Executor** plans with tool calls — maps to Antigravity tool-use execution
- `validate_action` is a native SDK function tool called by the Executor before finalizing each action step
- `POST /analyze { "flow_type": "google_sdk" }` uses the `google-genai` SDK's native function-calling loop
- `GET /export-trace` produces `nexus_antigravity_trace.json` — the full agent log, state snapshot, and decision flow submitted as the Antigravity trace artifact

---

## Setup

### Backend (required)

```bash
cd backend
pip install -r requirements.txt

# Copy and fill in credentials
cp .env.example .env   # or create .env manually (see Environment Variables below)

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Web Frontend

```bash
cd frontend-next
npm install
npm run dev       # development → http://localhost:3000
# or
npm run build && npm start   # production
```

> `.env.local` is already configured: `NEXT_PUBLIC_API_URL=http://localhost:8000`

### Mobile APK

```bash
cd nexus_mobile
flutter pub get
flutter build apk --release
# APK → nexus_mobile/build/app/outputs/flutter-apk/app-release.apk

# For emulator: backend URL is 10.0.2.2:8000 (already set in config.dart)
# For physical device: edit nexus_mobile/lib/config.dart → set your LAN IP
```

---

## Environment Variables

Create `backend/.env` with the following:

```env
# Gemini (required)
GOOGLE_API_KEY=your_google_ai_studio_key

# OpenRouter (optional — used before Gemini as primary LLM)
OPENROUTER_API_KEY=your_openrouter_key

# Step 2 — Real email notification
SMTP_USER=your_gmail@gmail.com
SMTP_PASS=your_16char_app_password
NOTIFY_EMAIL=recipient@example.com

# Step 3 — Real Google Sheets dashboard
GOOGLE_SHEET_ID=your_sheet_id_from_url
GOOGLE_SA_JSON={"type":"service_account",...}   # full service account JSON, one line

# Step 4 — Real Slack alert
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

If any integration variable is missing, that step falls back to a rich simulation — **the demo never crashes**.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System status + agent list |
| `POST` | `/ingest` | Ingest sources (form-data: text, csv_data, url, file, include_feed) |
| `POST` | `/analyze` | Run 5-agent pipeline (`flow_type`: custom \| google_sdk) |
| `POST` | `/execute` | Simulate action chain (email + Sheets + Slack) |
| `GET` | `/state` | Current pipeline state |
| `GET` | `/logs` | Execution log entries |
| `GET` | `/baseline-comparison` | NEXUS vs simple heuristic comparison |
| `POST` | `/what-if` | Re-run Executor with modified constraints |
| `GET` | `/export-trace` | Download full Antigravity trace JSON |
| `POST` | `/auth/register` · `/auth/login` | JWT authentication |

---

## Robustness Scenarios

All triggered automatically by the **Supply Chain seed**:

| Scenario | What happens |
|---|---|
| URL fetch failure | Source excluded, credibility scored 0.0, pipeline continues |
| Step 3 failure (40% random) | Google Sheets write fails → logged → retry → `RECOVERED` |
| Low-credibility source | Score < 0.30 → excluded before agents run |
| Contradiction detected | Two sources conflict → Resolver invoked → contradiction_resolution in output |
| Over-budget action | ConstraintChecker sets `was_modified: True`, adds `constraint_violations` |
| All LLM models fail | Realistic hardcoded fallback responses — demo never returns an error |

---

## Running the Tests

```bash
cd backend

# Fast tests (no LLM, ~4 min)
pytest test_challenge1.py test_pipeline.py -v -m "not llm"

# Full suite including LLM calls (~25 min)
pytest test_challenge1.py test_pipeline.py -v

# Just the end-to-end pipeline trace (with printed output)
pytest test_challenge1.py::TestFullPipelineScenario -v -s
```

**126 tests total · 125 pass · 1 skip** (Google Sheets real-write test — requires `gspread` + service account)

---

## Demo Video Script (Supply Chain, 3–5 min)

1. Start backend (`uvicorn main:app --port 8000`) + frontend (`npm run dev`)
2. Register / login on the web app
3. On **Dashboard** — paste the Supply Chain scenario text, upload the CSV, toggle Live Feed on
4. Click **Ingest** — show credibility matrix, contradiction card, temporal trend
5. Click **Analyze** — watch Orion / Raven / Cipher cards populate with agent insights
6. Show **DisagreementMeter** — confidence divergence between agents
7. Show **Resolver** synthesis with trusted evidence and investigation path
8. Show **ActionChain** — 5 causally-linked steps with cost / time / constraint status
9. Click **Execute** — Step 3 may flash red → amber RECOVERED
10. Show **Before / After** state diff
11. Open **Trace** page — show full execution log
12. Click **Export Trace** → `nexus_antigravity_trace.json` downloaded
13. Say: *"This JSON is our Antigravity submission artifact — every agent decision, every tool call, before and after state, full audit trail."*

---

## Assumptions

1. Gemini free tier (`gemini-2.5-flash-lite`) is sufficient for demo volume — 20 RPD limit; full suite stays under it with spacing
2. All scenario data is fictional and Pakistan-context inspired
3. Step 3 failure is simulated probabilistically (40%) — not every run triggers it
4. In-memory `state_store` resets on server restart — by design for demo simplicity
5. Constraints are hardcoded defaults; production would load from config

## Privacy

No real personal data. All scenarios fictional. No persistent storage beyond auth `users.json`.
