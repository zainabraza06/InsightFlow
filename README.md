# InsightFlow

**Autonomous multi-source intelligence → real-world action pipeline**

Built for Hackathon Challenge 1 · Google ADK + Gemini · OpenRouter · Groq · GCP Cloud Run · Vercel

---

## Live Deployment

| Service | URL |
|---------|-----|
| Web App | https://insight-flow-zainab.vercel.app |
| Backend API | https://insightflow-backend-481589186819.us-central1.run.app |
| API Docs | https://insightflow-backend-481589186819.us-central1.run.app/docs |
| Health Check | https://insightflow-backend-481589186819.us-central1.run.app/health |

---

## Problem Statement

Decision-makers in fast-moving environments (supply chain, operations, finance) receive information from many sources at once — CSV exports, news feeds, PDFs, field reports — that often contradict each other. There is no automated way to ingest all of it, detect conflicts, weigh source credibility, and generate a validated, executable action plan within minutes.

InsightFlow solves this end-to-end: it ingests unstructured multi-source data, runs a 5-agent AI debate to surface opportunities and risks, resolves contradictions, validates every action against real budget/time/staff constraints, and triggers live integrations — with no human in the loop.

## What It Does

InsightFlow ingests unstructured data from multiple sources (PDF, CSV, URL, text, live feed), runs a 5-agent parallel debate, resolves contradictions, validates every action against real-world constraints, and triggers live integrations — fully autonomous end-to-end.

```
Sources (PDF / CSV / URL / Text / Feed)
        │
        ▼
  Credibility Scoring  ──►  Contradiction Detection  ──►  Temporal Analysis
        │
        ▼
  ┌─────────────────────────────────────┐
  │  5-Agent Parallel Debate            │
  │                                     │
  │  Orion (Optimist)                   │
  │  Raven (Pessimist)   asyncio.gather │
  │  Cipher (Realist)                   │
  └──────────────┬──────────────────────┘
                 │
                 ▼
          Resolver  ──►  Executor  ──►  Constraint Checker
                                              │
                                              ▼
                              Step 2: Gmail SMTP (real email)
                              Step 3: Google Sheets (real write)
                              Step 4: Slack Webhook (real alert)
```

**LLM routing (every call):** OpenRouter → Groq → Vertex AI Gemini → AI Studio Gemini

---

## Mock vs Real APIs

A key design principle: every integration that can be real, is real. Simulated steps are clearly documented.

| Step | API / Service | Real or Mock | Details |
|------|--------------|:------------:|---------|
| LLM calls (all agents) | OpenRouter API | **Real** | HTTP to `openrouter.ai/api/v1/chat/completions` |
| LLM fallback 1 | Groq API | **Real** | HTTP to `api.groq.com/openai/v1/chat/completions` |
| LLM fallback 2 | Vertex AI Gemini | **Real** | GCP `google-genai` SDK, project `insightflow-496519` |
| LLM fallback 3 | Gemini AI Studio | **Real** | `google-genai` SDK with API key |
| Step 2 — Email alert | Gmail SMTP | **Real** | `smtplib` → port 587 TLS, real email delivered |
| Step 3 — Dashboard | Google Sheets | **Real** | `gspread` + Service Account, real row appended |
| Step 4 — Alert | Slack Webhook | **Real** | HTTP POST to workspace, real message posted |
| Step 1 — Diagnosis | Root cause analysis | Simulated | Structured text from Resolver output |
| Step 5 — Monitoring | Schedule setup | Simulated | Structured monitoring plan returned as JSON |
| Live feed ingestion | Supply chain signals | Simulated | Domain-keyed hardcoded signals (demo seed data) |
| PDF ingestion | PyMuPDF | **Real** | Full text extraction from uploaded PDF bytes |
| URL ingestion | httpx | **Real** | Live HTTP fetch, HTML stripped |
| CSV ingestion | csv.DictReader | **Real** | Parsed with temporal column auto-detection |

---

## Agent System Design

### Google ADK Integration

The backend uses **Google Agent Development Kit (ADK)** as a structured agent runtime. Each of the five agents is wrapped in an ADK `Agent` object with a defined system prompt and tool set. ADK handles prompt formatting, model selection, and structured output parsing. If ADK is not installed, the system gracefully falls back to direct Gemini API calls — no code changes required.

ADK agents are defined in `backend/agents.py` and used for the `flow_type="custom"` pipeline (default). An alternative `flow_type="google_sdk"` route in `sdk_agents.py` uses the Gen AI SDK natively for comparison.

### The Five Agents

**Orion — Optimist Analyst**
- Persona: Identifies hidden opportunities, first-mover advantages, and positive signals buried in crisis data
- Input: Combined source text (600 chars/source) + domain + credibility map + learning context from past feedback
- Output JSON: `{insight, impact, recommended_action, confidence, key_signal}`
- Weight in consensus: 30%

**Raven — Pessimist Analyst**
- Persona: Surfaces worst-case risks, cascade failure points, and scenarios other analysts miss
- Input: Same as Orion
- Output JSON: `{insight, impact, recommended_action, confidence, key_signal}`
- Weight in consensus: 30%

**Cipher — Realist Analyst**
- Persona: Probability-weighted assessment with confidence intervals. Refuses to speculate without evidence.
- Input: Same as Orion
- Output JSON: `{insight, impact, recommended_action, confidence, key_signal}`
- Weight in consensus: 40% (highest — ground truth anchor)

**Resolver — Synthesis Engine**
- Input: All three analyst outputs + contradiction report + temporal analysis
- Role: Reconciles disagreements, ranks evidence by credibility, produces a single authoritative finding
- Output JSON: `{final_insight, trusted_evidence, situation_summary, contradiction_resolution, recommended_priority}`

**Executor — Action Planner**
- Input: Resolver output + user constraints (budget, time, staff, urgency)
- Role: Produces a causal 5-step action chain where each step has a `triggered_by` and `enables` link
- Output JSON: `[{step, action, triggered_by, enables, estimated_cost_pkr, estimated_time_minutes}]`

### Parallel Execution

Orion, Raven, and Cipher run concurrently via `asyncio.gather` with a 1.2s stagger between each to prevent simultaneous rate limiting on free-tier APIs. Resolver and Executor run sequentially after all three analysts complete.

### LLM Routing (every agent call)

```
1. OpenRouter (primary, free tier)
   └─ llama-3.3-70b-instruct → deepseek-v4-flash → gemma-4-31b → llama-3.2-3b
   └─ 429 rate limit → retry once with 3s backoff, then next provider

2. Groq (secondary, free tier, 5-10x faster)
   └─ llama-3.3-70b-versatile → llama-3.1-70b-versatile → mixtral-8x7b → llama-3.1-8b

3. Vertex AI Gemini (GCP credits)
   └─ gemini-2.0-flash → gemini-2.0-flash-lite → gemini-1.5-flash

4. AI Studio Gemini (API key fallback)
   └─ Same model cascade as Vertex AI
```

JSON robustness: all agent responses parsed with `JSONDecoder.raw_decode()` which finds the first valid JSON object at any position in the response — handles models that wrap JSON in prose ("Here is the analysis: {...}").

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Mobile | Flutter 3.x, Dart |
| Backend | FastAPI, Python 3.11, uvicorn |
| Primary LLM | OpenRouter free tier — llama-3.3-70b, deepseek-v4-flash, gemma-4-31b, llama-3.2-3b |
| LLM Provider 2 | Groq — llama-3.3-70b-versatile, mixtral-8x7b, llama-3.1-8b |
| LLM Fallback | Google Gemini via Vertex AI (GCP) or AI Studio |
| AI Runtime | Google ADK (graceful fallback if not installed) |
| Auth | JWT (PyJWT), SHA-256 + salt |
| Ingestion | PyMuPDF (PDF), httpx (URL), csv.DictReader (CSV) |
| Real Actions | smtplib (Gmail), gspread (Sheets), httpx (Slack) |
| Storage (prod) | Google Cloud Firestore (Native mode) |
| Storage (dev) | JSON flat files |
| Hosting (backend) | GCP Cloud Run (us-central1) |
| Hosting (frontend) | Vercel |
| Secrets | GCP Secret Manager |

---

## Architecture

### Pipeline — 7 Phases

**Phase 1 — Ingestion**

| Source | Processing | Credibility Base |
|--------|-----------|-----------------|
| PDF | PyMuPDF text extraction | 0.85 |
| CSV | DictReader + temporal detection | 0.90 |
| URL | HTTP fetch, HTML stripped | 0.70 |
| Text | Raw pass-through | 0.65 |
| Feed | Domain-keyed signal | 0.60 |

**Phase 2 — Credibility Scoring**

Scores adjusted per source:
- `+0.10` PDF type · `+0.05` CSV · `+0.05` temporal columns
- `-0.15` noisy terms (breaking/rumor/unconfirmed) · `-0.20` stale terms
- `< 0.30` → excluded · `0.30–0.50` → low-confidence · `≥ 0.50` → trusted

**Phase 3 — Contradiction Detection** (OpenRouter → Groq → Gemini)

Cross-source conflict detection with trust ranking, stale/noise flagging, temporal trend analysis, and 3-step investigation paths per conflict. Robust JSON parser using `raw_decode()` handles prose-wrapped LLM responses.

**Phase 4 — 5-Agent Parallel Debate**

All three analysts run concurrently via `asyncio.gather` with 1.2s stagger to avoid rate limiting:

| Agent | Role | Weight |
|-------|------|--------|
| Orion | Optimist — hidden opportunities, first-mover advantage | 30% |
| Raven | Pessimist — worst-case risks, cascade failures | 30% |
| Cipher | Realist — probability-weighted, confidence intervals | 40% |
| Resolver | Synthesizes all three into a single authoritative finding | — |
| Executor | Plans a 5-step causal action chain | — |

**Phase 5 — Constraint Validation** (pure Python, zero API calls)

Checks each step: cost vs budget, time vs max hours × urgency multiplier, staff vs available. Urgency multipliers: `low=1.5` · `medium=1.0` · `high=0.7` · `critical=0.4`

**Phase 6 — Chain Execution**

- Step 1: Root cause diagnosis (simulated)
- Step 2: Gmail SMTP → real email to `NOTIFY_EMAIL`
- Step 3: Google Sheets → real row write via Service Account
- Step 4: Slack Webhook → real HTTP POST to workspace
- Step 5: Monitoring schedule (simulated)

**Phase 7 — Feedback Learning Loop**

User ratings (1–5) stored per domain. Last 15 ratings injected as `learning_context` into every future agent prompt.

---

## Quick Start (Local Dev)

### Prerequisites

- Python 3.10+
- Node.js 18+
- Flutter 3.x (mobile only)
- [Gemini API key](https://aistudio.google.com/app/apikey)
- [OpenRouter API key](https://openrouter.ai/keys) — free tier
- [Groq API key](https://console.groq.com) — free tier

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:

```env
GOOGLE_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key
GROQ_API_KEY=your_groq_key

# Optional — Steps 2-4 fall back to simulation without these
SMTP_USER=your@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx    # Gmail App Password (16 chars, requires 2FA)
NOTIFY_EMAIL=recipient@example.com
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_SA_JSON={"type":"service_account",...}   # single line, \n for newlines
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

NEXUS_BASE_URL=http://localhost:8000
```

```bash
uvicorn main:app --reload
# API:  http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Web Frontend

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
# http://localhost:3000
```

### Mobile

```bash
cd nexus_mobile
flutter create --platforms=android .
flutter pub get
flutter run
```

For production, `lib/config.dart` already points to the deployed backend.

---

## Deployment

### Backend — GCP Cloud Run

The backend is containerized via `Dockerfile` and deployed to Cloud Run. All secrets are stored in GCP Secret Manager and injected at runtime — no secrets ever enter the container image.

```bash
cd backend
gcloud run deploy insightflow-backend \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --set-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest,..." \
  --set-env-vars "GCP_PROJECT=insightflow-496519,GCP_LOCATION=us-central1,FIRESTORE_ENABLED=true"
```

See `GCP_DEPLOY.md` for the full step-by-step guide including IAM roles, Secret Manager setup, and Firestore configuration.

### Frontend — Vercel

Deployed automatically from the `frontend-next/` directory. Environment variable `NEXT_PUBLIC_API_URL` points to the Cloud Run backend URL.

### Storage — Firestore vs JSON

| Mode | When | How |
|------|------|-----|
| Firestore | `FIRESTORE_ENABLED=true` | Collections: `users`, `history`, `feedback` |
| JSON files | default (local dev) | `users.json`, `history.json`, `feedback.json` |

No code changes needed — the env var switches the backend transparently.

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register `{name, email, password}` |
| POST | `/auth/login` | Login → JWT token |
| GET | `/auth/me` | Current user (JWT) |
| PUT | `/auth/me` | Update name or password |

### Core Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest` | Ingest sources → credibility + contradictions |
| POST | `/analyze` | Run 5-agent debate → action chain |
| POST | `/execute` | Execute action chain (real integrations) |
| POST | `/what-if` | Re-run Executor with modified constraints |

### History & Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST/GET | `/history` | Save or list analysis entries |
| GET/DELETE | `/history/{id}` | Get or delete a specific entry |
| POST | `/feedback` | Submit rating + comment |
| GET | `/feedback/stats` | Global domain statistics |
| GET | `/feedback/domain/{domain}` | Domain learning context |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Status + agent list |
| GET | `/state` | Current pipeline snapshot |
| GET | `/baseline-comparison` | InsightFlow vs simple heuristic |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/users` | All users |
| GET | `/admin/dashboard-stats` | Aggregate stats |
| POST | `/admin/toggle-role` | Toggle admin role |
| DELETE | `/admin/history/{id}` | Delete any entry |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini API key (AI Studio fallback) |
| `OPENROUTER_API_KEY` | Recommended | Primary LLM — free tier |
| `GROQ_API_KEY` | Recommended | Secondary LLM — free tier, faster |
| `GCP_PROJECT` | Cloud only | GCP project ID for Vertex AI |
| `GCP_LOCATION` | Cloud only | GCP region (e.g. `us-central1`) |
| `FIRESTORE_ENABLED` | Cloud only | Set `true` to use Firestore instead of JSON |
| `NEXUS_BASE_URL` | Yes | Backend URL (self-reference for orchestration) |
| `SMTP_USER` | Optional | Gmail address for Step 2 email alerts |
| `SMTP_PASS` | Optional | Gmail App Password (16 chars, requires 2FA) |
| `NOTIFY_EMAIL` | Optional | Recipient for Step 2 alerts |
| `GOOGLE_SHEET_ID` | Optional | Sheet ID for Step 3 state updates |
| `GOOGLE_SA_JSON` | Optional | Service account JSON as single line |
| `SLACK_WEBHOOK_URL` | Optional | Slack webhook for Step 4 alerts |

---

## Live Test Results

**Run:** May 19 2026 · 3 sources (CSV + URL + Raw Text) · urgency=high · budget=PKR 600,000

**Ingestion**
- Credibility: `text=0.65` · `url=0.70` · `csv=1.00` — all 3 trusted
- Contradiction: TEXT (May 18 notice, 80 units) vs CSV (March, 1200 units) — TEXT trusted as more recent
- Trend: worsening — SKU-001 stock 1200 → 600 → 200 → 80 units (March through May)

**Agent Debate**
- Orion 85% — 40% Punjab supplier coverage, 48h window
- Raven 92% — zero SKU-002, complete shutdown within 14 days
- Cipher 92% — 90% probability halt within 48h without intervention
- Weighted confidence: **86.6%**

**Action Chain** (per-step limit: PKR 120k / 50 min)

| Step | Status | Cost | Time | Note |
|------|--------|------|------|------|
| 1 — Verify stock across warehouses | MODIFIED | PKR 15,000 | 90 min | Time exceeded |
| 2 — Exec + procurement alert | MODIFIED | PKR 10,000 | 60 min | Time exceeded |
| 3 — Update ERP, halt orders | OK | PKR 8,000 | 45 min | |
| 4 — Global procurement + air cargo | MODIFIED | PKR 150,000 | 120 min | Cost + time exceeded |
| 5 — Daily crisis monitoring | OK | PKR 12,000 | 45 min | |

Total: PKR 195,000 / PKR 600,000 · 3/5 steps flagged

**Real Integrations**
- Step 2: real email via Gmail SMTP
- Step 3: real row written to Google Sheets
- Step 4: real Slack webhook (HTTP 200)
- Total latency: 25,547ms

---

## Project Structure

```
aiseekho/
├── backend/
│   ├── main.py              # FastAPI app — 26 endpoints, CORS, auth middleware
│   ├── agents.py            # Orion, Raven, Cipher, Resolver, Executor + LLM routing
│   ├── ingestion.py         # PDF, text, URL, CSV, feed processors
│   ├── contradiction.py     # Credibility scoring + contradiction detection
│   ├── constraints.py       # Pure Python constraint checker
│   ├── simulator.py         # Chain executor + real integrations
│   ├── real_actions.py      # Gmail SMTP, Google Sheets, Slack webhook
│   ├── auth.py              # JWT + SHA-256+salt + admin roles
│   ├── history_store.py     # Per-user history (Firestore or JSON)
│   ├── feedback_store.py    # Domain feedback + learning context
│   ├── Dockerfile           # Cloud Run container
│   └── requirements.txt
│
├── frontend-next/
│   └── src/
│       ├── app/             # Next.js App Router pages
│       └── components/
│           ├── analysis/    # AgentDebate, ActionChain, FeedbackWidget
│           └── ui/          # Button, Badge, Card, Input, LoadingSpinner
│
├── nexus_mobile/
│   └── lib/
│       ├── screens/         # login, register, input, debate, chain, history
│       ├── services/        # api_service.dart, auth_service.dart
│       └── config.dart      # Base URL (points to Cloud Run in production)
│
└── GCP_DEPLOY.md            # Full GCP deployment guide
```

---

## Hackathon Checklist

- [x] Multi-source ingestion — PDF, text, CSV, URL, feed
- [x] Credibility scoring — deterministic per-source
- [x] Noise filtering — excluded below 0.30 threshold
- [x] Contradiction detection — cross-source conflicts with trust ranking
- [x] Temporal trend analysis — improving / worsening / stable + rate-of-change
- [x] 5-agent parallel debate — Orion + Raven + Cipher via `asyncio.gather`
- [x] Resolver synthesis — single authoritative finding from 3 agents
- [x] Constraint validation — budget / time / staff / urgency (pure Python)
- [x] 5-step causal action chain — triggered_by + enables
- [x] Real integrations — Gmail SMTP, Google Sheets, Slack Webhook
- [x] What-if counterfactual analysis
- [x] Agent learning loop — feedback ratings injected per domain
- [x] Web frontend — Next.js 14 + TypeScript + Tailwind, dark theme
- [x] Mobile app — Flutter, full feature parity
- [x] JWT authentication — SHA-256+salt, per-user history
- [x] Admin panel — user management, feedback stats, domain breakdown
- [x] Deployed — GCP Cloud Run (backend) + Vercel (frontend) + Firestore (storage)
- [x] OpenRouter primary + Groq secondary + Vertex AI fallback LLM chain
- [x] Robust JSON parser — `raw_decode()` handles prose-wrapped responses
- [x] Rate-limit retry — 429 responses retried with backoff per model
