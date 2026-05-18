# InsightFlow — Autonomous Content-to-Action Intelligence

> **Hackathon Challenge 1** — Autonomous Content-to-Action Agent  
> Developed in **Antigravity AI IDE** · Runtime powered by **Google ADK + Gemini 2.0 Flash**

InsightFlow transforms unstructured multi-source intelligence into an executed, constraint-validated action chain — using a 5-agent debate system that detects contradictions, resolves uncertainty, and triggers real-world integrations automatically.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      InsightFlow v2.0                           │
├──────────────┬──────────────────────────┬───────────────────────┤
│  Next.js 14  │    FastAPI Backend        │   Flutter Mobile      │
│  (Web UI)    │    (Python 3.14)          │   (iOS / Android)     │
└──────┬───────┴──────────┬───────────────┴───────────┬───────────┘
       └──────────────────┼────────────────────────────┘
                          │  REST API (localhost:8000)
          ┌───────────────▼───────────────────────────┐
          │              Agent Pipeline                │
          │  ┌──────┐  ┌──────┐  ┌──────┐            │
          │  │Orion │  │Raven │  │Cipher│  (parallel) │
          │  │Optim.│  │Pess. │  │Real. │             │
          │  └──┬───┘  └──┬───┘  └──┬───┘            │
          │     └─────────┴──────────┘                │
          │              ┌──────▼──────┐              │
          │              │  Resolver   │  (synthesis)  │
          │              └──────┬──────┘              │
          │              ┌──────▼──────┐              │
          │              │  Executor   │  (chain)      │
          │              └─────────────┘              │
          └───────────────────────────────────────────┘
```

### LLM Call Priority (per request)
1. **OpenRouter** (free tier) — `google/gemini-2.0-flash-exp:free` → `meta-llama/llama-3.1-8b-instruct:free` → fallbacks
2. **Google ADK** — if `google-adk` package is installed
3. **Direct Gemini** — `gemini-1.5-flash` → `gemini-2.0-flash-lite` → `gemini-2.0-flash`

---

## Features

### 5-Agent Debate System
| Agent | Role | Persona |
|-------|------|---------|
| **Orion** | Optimist Analyst | Finds hidden opportunities, first-mover advantages |
| **Raven** | Pessimist Analyst | Identifies worst-case risks and failure points |
| **Cipher** | Realist Analyst | Probability-weighted assessment with confidence intervals |
| **Resolver** | Synthesis Engine | Reconciles agent conflicts into one authoritative insight |
| **Executor** | Action Planner | Generates 5-step causal chain with constraint validation |

### Intelligence Pipeline (7 Phases)
1. **Content Ingestion** — PDF, text, CSV, URL, live RSS feed (5 source types)
2. **Credibility Scoring** — Each source scored 0–1, low-credibility sources filtered
3. **Contradiction Detection** — Cross-source conflict identification with severity rating
4. **Temporal Analysis** — Trend direction (improving/worsening/stable) from time-series data
5. **Agent Debate** — Orion + Raven + Cipher run in parallel via `asyncio.gather`
6. **Constraint Validation** — Budget / time / staff / urgency checked per action step
7. **Chain Execution** — Real integrations: email (SMTP) → Google Sheets → Slack webhook

### Agent Learning Loop
- Users rate analyses 1–5 (emoji feedback widget on web and mobile)
- Last 15 ratings per domain stored in `feedback.json`
- Negative feedback → agents instructed to "cite sources, name specific entities"
- Positive feedback → agents told to "maintain this reasoning style"
- Learning context injected into every Gemini prompt for that domain

### Real-World Integrations
| Step | Integration | Trigger |
|------|------------|---------|
| Step 2 | Gmail SMTP | Stakeholder alert email |
| Step 3 | Google Sheets | System state dashboard update |
| Step 4 | Slack Webhook | Mitigation alert notification |

### What-If Analysis
Counterfactual constraint re-runs — modify budget/urgency/staff and see how the action chain changes without re-running agents.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Web Frontend** | Next.js 14, TypeScript, Tailwind CSS, App Router |
| **Mobile** | Flutter 3.x, Dart |
| **Backend** | FastAPI, Python 3.14, uvicorn |
| **AI Runtime** | Google ADK, google-generativeai (Gemini 2.0 Flash) |
| **Secondary LLM** | OpenRouter (free tier) |
| **Auth** | JWT (PyJWT), SHA-256+salt password hashing |
| **Storage** | JSON flat files (users, history, feedback) |
| **Development IDE** | Antigravity AI |

---

## Project Structure

```
insightflow/
├── backend/                    # FastAPI backend
│   ├── main.py                 # API endpoints (auth, ingest, analyze, execute, history, feedback)
│   ├── agents.py               # 5-agent system + Google ADK integration
│   ├── ingestion.py            # Multi-source ingestion engine
│   ├── contradiction.py        # Cross-source contradiction detector
│   ├── constraints.py          # Budget/time/staff constraint checker
│   ├── simulator.py            # Action chain executor with failure recovery
│   ├── auth.py                 # JWT auth + SHA-256 hashing
│   ├── history_store.py        # Per-user analysis history (max 50)
│   ├── feedback_store.py       # Domain feedback + learning context
│   ├── requirements.txt
│   └── .env                    # API keys (never commit)
│
├── frontend-next/              # Next.js 14 web app
│   └── src/
│       ├── app/
│       │   ├── (auth)/         # Login, Register
│       │   └── (protected)/    # Dashboard, Analyze, History, Trace, Settings
│       ├── components/
│       │   ├── analysis/       # AgentDebate, ActionChain, FeedbackWidget, RiskTimeline
│       │   ├── layout/         # Sidebar, Navbar
│       │   └── ui/             # Button, Card, Badge, Input, LoadingSpinner
│       └── lib/                # api.ts, auth.ts
│
├── nexus_mobile/               # Flutter mobile app
│   └── lib/
│       ├── screens/            # Input, Debate, Chain, Execution, History, HistoryDetail, Settings
│       └── services/           # ApiService, AuthService
│
└── antigravity_trace.json      # Execution trace (load in Trace Viewer)
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Flutter 3.x (for mobile)
- Gemini API key from [aistudio.google.com](https://aistudio.google.com/app/apikey)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:
```env
GOOGLE_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key   # recommended — reduces Gemini quota usage

# Optional real-world integrations
SMTP_USER=your@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx            # Gmail App Password (requires 2FA)
NOTIFY_EMAIL=recipient@example.com
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_SA_JSON={"type":"service_account",...}  # paste as single line
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

```bash
uvicorn main:app --reload
# API: http://localhost:8000
# Swagger docs: http://localhost:8000/docs
```

### 2. Web Frontend

```bash
cd frontend-next
npm install
```

Create `frontend-next/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

```bash
npm run dev
# App: http://localhost:3000
```

### 3. Mobile

```bash
cd nexus_mobile
flutter pub get
```

Edit `lib/config.dart` — set your backend URL:
```dart
// Android emulator
static const String baseUrl = 'http://10.0.2.2:8000';
// iOS simulator / physical device on same network
// static const String baseUrl = 'http://192.168.x.x:8000';
```

```bash
flutter run
```

---

## API Reference

### Auth
| Method | Endpoint | Body | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | `{name, email, password}` | Create account |
| POST | `/auth/login` | `{email, password}` | Sign in → `{token, user}` |
| GET | `/auth/me` | — | Current user (JWT required) |
| PUT | `/auth/me` | `{name?, password?}` | Update profile (JWT required) |

### Analysis Pipeline
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest` | Ingest sources (multipart: text, url, file, csv_data, domain, topic) |
| POST | `/analyze` | Run 5-agent consensus `{domain, constraints}` |
| POST | `/execute` | Execute action chain `{domain}` |
| POST | `/what-if` | Counterfactual analysis `{modifications}` |
| GET | `/state` | Current system state snapshot |
| GET | `/export-trace` | Download execution trace JSON |

### History & Feedback
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/history` | Save analysis entry (JWT required) |
| GET | `/history` | List user history summaries (JWT required) |
| GET | `/history/{id}` | Full detail with agents + chain (JWT required) |
| DELETE | `/history/{id}` | Delete entry (JWT required) |
| POST | `/feedback` | Submit rating + comment `{rating, domain, comment, analysis_id}` |
| GET | `/feedback/stats` | Global domain statistics |
| GET | `/feedback/domain/{domain}` | Domain learning context |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | ✅ Yes | Gemini API key |
| `OPENROUTER_API_KEY` | Recommended | OpenRouter free tier (reduces Gemini quota usage) |
| `SMTP_USER` | Optional | Gmail address for stakeholder alerts |
| `SMTP_PASS` | Optional | Gmail App Password (16 chars, requires 2FA) |
| `NOTIFY_EMAIL` | Optional | Email to receive stakeholder alerts |
| `GOOGLE_SHEET_ID` | Optional | Google Sheet for system state dashboard |
| `GOOGLE_SA_JSON` | Optional | Service account JSON (single line, newlines as `\n`) |
| `SLACK_WEBHOOK_URL` | Optional | Slack incoming webhook for mitigation alerts |

---

## Antigravity IDE

InsightFlow was built and iterated inside the **Antigravity AI IDE**. The runtime product is fully standalone — Antigravity is not a dependency. The `antigravity_trace.json` file documents the full development workplan and 23 execution events. Load it in the **Trace Viewer** (`/trace`) to inspect agent phases, tool calls, and decision reasoning.

---

## Hackathon Checklist

- [x] Multi-source ingestion (PDF, text, CSV, URL, RSS feed)
- [x] Credibility scoring and noise filtering
- [x] Contradiction detection with severity levels
- [x] Temporal trend analysis
- [x] 5-agent parallel debate (Orion, Raven, Cipher, Resolver, Executor)
- [x] Constraint validation (budget, time, staff, urgency)
- [x] 5-step causal action chain
- [x] Real integrations (Gmail SMTP, Google Sheets, Slack Webhook)
- [x] What-if counterfactual analysis
- [x] Agent learning loop from user feedback
- [x] Web frontend (Next.js 14 + TypeScript)
- [x] Mobile app (Flutter — iOS & Android)
- [x] JWT authentication + history per user
- [x] Antigravity trace viewer
- [x] Google ADK integration with graceful fallback
- [x] OpenRouter as primary LLM (Gemini as fallback)
