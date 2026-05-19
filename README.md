# InsightFlow — Autonomous Content-to-Action Intelligence

> **Hackathon Challenge 1** — Autonomous Content-to-Action Agent
> Runtime: **Google ADK + Gemini 2.0 Flash** · Primary LLM: **OpenRouter (free tier)**
> Built in **Antigravity AI IDE**

InsightFlow ingests unstructured multi-source intelligence, runs a 5-agent parallel debate, resolves contradictions, validates every action against real constraints, and triggers real-world integrations — fully autonomous end-to-end.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Full Pipeline — 7 Phases](#full-pipeline--7-phases)
3. [Agent System](#agent-system)
4. [API Reference — All 26 Endpoints](#api-reference--all-26-endpoints)
5. [Feature Matrix — Web vs Mobile](#feature-matrix--web-vs-mobile)
6. [Tech Stack](#tech-stack)
7. [Project Structure](#project-structure)
8. [Quick Start](#quick-start)
9. [Environment Variables](#environment-variables)
10. [Live Test Results](#live-test-results)
11. [Hackathon Checklist](#hackathon-checklist)

---

## Architecture

```
+-------------------------------------------------------------------------+
|                         InsightFlow v2.0                                |
+------------------+---------------------------+---------------------------+
|  Next.js 14      |    FastAPI Backend         |   Flutter Mobile          |
|  (Web UI)        |    Python 3.14            |   iOS / Android           |
|  port 3000       |    port 8000              |                           |
+--------+---------+-------------+-------------+------------------+--------+
         |                       |                                |
         +-----------------------+--------------------------------+
                                 |   REST API (HTTP/JSON)
                                 |   multipart/form-data
          +----------------------v--------------------------------------------+
          |                   InsightFlow Backend                              |
          |                                                                    |
          |  POST /ingest -----> IngestionEngine                              |
          |                           |                                        |
          |                           v                                        |
          |                  ContradictionEngine                               |
          |              (OpenRouter -> Gemini fallback)                       |
          |                           |                                        |
          |                           v                                        |
          |  POST /analyze ----> ConsensusEngine                              |
          |                                                                    |
          |   +----------+   +----------+   +---------+                       |
          |   |  Orion   |   |  Raven   |   | Cipher  |   <-- asyncio.gather  |
          |   | Optimist |   |Pessimist |   | Realist |                       |
          |   +----+-----+   +----+-----+   +----+----+                       |
          |        +---------------+--------------+                            |
          |                        v                                           |
          |                 +-----------+                                      |
          |                 | Resolver  |  synthesize                          |
          |                 +-----+-----+                                      |
          |                       v                                            |
          |                 +-----------+                                      |
          |                 | Executor  |  plan chain                          |
          |                 +-----+-----+                                      |
          |                       v                                            |
          |             ConstraintChecker                                      |
          |          (pure Python math, zero API calls)                       |
          |                       |                                            |
          |  POST /execute ----> ActionSimulator                              |
          |                  +---+------------------------+                    |
          |                  | Step 2: Gmail SMTP         |                    |
          |                  | Step 3: Google Sheets      |                    |
          |                  | Step 4: Slack Webhook      |                    |
          |                  +----------------------------+                    |
          +--------------------------------------------------------------------+

LLM Call Priority (every agent prompt):
  1. OpenRouter  --- llama-3.3-70b -> deepseek-v4-flash -> gemma-4-31b -> llama-3.2-3b
  2. Google ADK  --- if google-adk installed (graceful fallback if not)
  3. Gemini direct - gemini-2.5-flash-lite -> gemini-2.5-flash -> gemini-2.0-flash
```

---

## Full Pipeline — 7 Phases

```
PHASE 1 — CONTENT INGESTION
-------------------------------------------------------------
IngestionEngine processes each source:

  Source    Processing                    Credibility Base
  --------  ----------------------------  ----------------
  PDF       PyMuPDF text extraction       0.85
  Text      Word count, raw pass-through  0.65
  URL       HTTP fetch, HTML stripped     0.70
  CSV       DictReader, temporal detect   0.90
  Feed      Domain-keyed signal (demo)    0.60

PHASE 2 — CREDIBILITY SCORING
-------------------------------------------------------------
ContradictionEngine.score_credibility() adjusts each source:
  +0.10  PDF type
  +0.05  CSV type
  +0.05  temporal columns (date/month/week/day)
  -0.15  noisy terms (breaking/rumor/unconfirmed/allegedly)
  -0.20  stale terms (yesterday/last week/last month)
   0.00  URL fetch failed

  Filter:  score < 0.30 -> excluded
           0.30-0.50    -> low-confidence (still used)
           >= 0.50      -> trusted

PHASE 3 — CONTRADICTION DETECTION  (OpenRouter -> Gemini)
-------------------------------------------------------------
  - Find cross-source conflicting claims on same metric
  - Trust ranking by recency + specificity + credibility
  - Flag stale / noisy sources
  - Temporal trend analysis (improving/worsening/stable)
  - Investigation path (3 steps per conflict)
  Robust parser: raw_decode() finds first JSON block in prose

PHASE 4 — 5-AGENT PARALLEL DEBATE
-------------------------------------------------------------
  asyncio.gather(Orion, Raven, Cipher) — all three in parallel
  Each gets: combined_text (600 chars/source) + domain
             + credibility_map + learning_context
  Routing:   OpenRouter -> ADK -> Gemini direct
  Retry:     429 rate-limits retried once per model
  Parser:    raw_decode() handles prose-wrapped responses

  Orion  (Optimist) -- hidden opportunity, first-mover advantage
  Raven  (Pessimist)-- worst-case risks, cascade failure points
  Cipher (Realist)  -- probability-weighted, confidence intervals
  Weighted confidence: Cipher*0.40 + Orion*0.30 + Raven*0.30

  Then: Resolver synthesizes -> Executor plans 5-step chain

PHASE 5 — CONSTRAINT VALIDATION  (pure Python, zero API calls)
-------------------------------------------------------------
  per_step_budget = total_budget_pkr / 5
  per_step_time   = (max_hours / 5) * urgency_multiplier
    urgency: low=1.5  medium=1.0  high=0.7  critical=0.4

  Checks: cost > per_step_budget     -> was_modified=True
          time_hours > per_step_time -> was_modified=True
          staff > available_staff    -> was_modified=True

PHASE 6 — CHAIN EXECUTION  (POST /execute)
-------------------------------------------------------------
  Step 1  Diagnose  root cause analysis (simulated)
  Step 2  Notify    Gmail SMTP -> real email to NOTIFY_EMAIL
  Step 3  Update    Google Sheets -> real row via Service Account
  Step 4  Mitigate  Slack Webhook -> real HTTP POST to workspace
  Step 5  Monitor   monitoring schedule (simulated)

  Each step: transaction ID, cost + latency tracking
  Failure recovery: failed steps retried once, degraded action

PHASE 7 — FEEDBACK LEARNING LOOP
-------------------------------------------------------------
  User rates 1-5 -> feedback_store saves rating + comment
  Last 15 ratings per domain retained

  learning_context injected into every future agent prompt:
    avg < 3  -> "Users frustrated. Cite sources, name entities."
    avg >= 4 -> "Users satisfied. Maintain this style."
    mixed    -> "Improve specificity. Add numbers and evidence."
```

---

## Agent System

| Agent | Role | Persona | Key Output |
|-------|------|---------|-----------|
| **Orion** | Optimist Analyst | Hidden opportunities, first-mover | insight, impact, recommended_action, confidence, key_signal |
| **Raven** | Pessimist Analyst | Worst-case risks, cascade failures | insight, impact, recommended_action, confidence, key_signal |
| **Cipher** | Realist Analyst | Probability-weighted, intervals | insight, impact, recommended_action, confidence, key_signal |
| **Resolver** | Synthesis Engine | Reconciles conflicts | final_insight, trusted_evidence, situation_summary, contradiction_resolution |
| **Executor** | Action Planner | 5-step causal chain | step, action, triggered_by, enables, estimated_cost_pkr, estimated_time_minutes |

---

## API Reference — All 26 Endpoints

### Authentication

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| POST | `/auth/register` | `{name, email, password}` | `{token, user}` |
| POST | `/auth/login` | `{email, password}` | `{token, user}` |
| GET | `/auth/me` | — (JWT) | `{id, name, email, is_admin}` |
| PUT | `/auth/me` | `{name?, password?}` (JWT) | `{updated: true}` |

### Ingestion

| Method | Endpoint | Form Fields | Response |
|--------|----------|-------------|----------|
| POST | `/ingest` | `text, url, csv_data, domain, topic, include_feed, file(PDF)` | `{sources_processed, credibility_map, contradictions_found, contradictions, temporal_analysis}` |

### Analysis

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| POST | `/analyze` | `{domain, constraints, flow_type?}` | `{agents[], weighted_confidence, resolved, action_chain[], total_estimated_cost_pkr, learning_active}` |

**Default constraints:** `budget_pkr=500000, max_response_time_hours=4, available_staff=3, urgency="medium"`
**flow_type:** `"custom"` (ADK-backed, default) or `"google_sdk"` (Gen AI SDK native)

### Execution & What-If

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| POST | `/execute` | `{chain[], domain}` | `{chain[], failures, recovered, total_cost_pkr, total_latency_ms, execution_log[]}` |
| POST | `/what-if` | `{modifications:{budget_pkr?, urgency?, ...}}` | `{action_chain[], cost_delta_pkr, actions_modified, feasibility_summary}` |

### History

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/history` | JWT | Save analysis entry |
| GET | `/history` | JWT | List user's entries (summary) |
| GET | `/history/{id}` | JWT | Full entry with agent debate + chain |
| DELETE | `/history/{id}` | JWT | Delete entry |

### Feedback

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/feedback` | JWT | Submit `{rating, domain, comment, analysis_id}` |
| GET | `/feedback/stats` | JWT | Global domain statistics |
| GET | `/feedback/my` | JWT | User's own feedback |
| GET | `/feedback/domain/{domain}` | JWT | Domain learning context |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Status, agent list, capabilities |
| GET | `/state` | Current pipeline state snapshot |
| GET | `/logs` | Execution log from current run |
| GET | `/baseline-comparison` | InsightFlow vs simple heuristic |

### Admin (admin role required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/users` | All users with roles |
| GET | `/admin/history` | All history across all users |
| GET | `/admin/feedback` | All feedback entries |
| GET | `/admin/dashboard-stats` | Aggregate: users, runs, cost, domains |
| POST | `/admin/toggle-role` | Toggle user admin `{email}` |
| DELETE | `/admin/history/{id}` | Delete any entry |
| POST | `/admin/reset-feedback` | Clear all domain feedback |

---

## Feature Matrix — Web vs Mobile

| Feature | Web | Mobile |
|---------|:---:|:------:|
| Login / Register | Yes | Yes |
| Multi-source ingestion (text, URL, CSV, feed, PDF) | Yes | Yes |
| Quick seed presets (sales, fuel, supply) | Yes | Yes |
| Topic field | Yes | Yes |
| Constraint configuration (budget, time, staff, urgency) | Yes | Yes |
| Source credibility scores | Yes | Yes |
| Contradiction detection display | Yes | Yes |
| Temporal trend analysis | Yes | Yes |
| 5-agent debate view | Yes | Yes |
| Weighted confidence score | Yes | Yes |
| Resolver synthesis | Yes | Yes |
| Action chain with constraint badges | Yes | Yes |
| Real execution (email, sheets, Slack) | Yes | Yes |
| Execution log | Yes | Yes |
| What-if analysis API | Yes | Yes |
| History list + detail view | Yes | Yes |
| Feedback / learning widget | Yes | Yes |
| Baseline comparison | Yes | Yes |
| Admin panel | Yes | — |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Web Frontend** | Next.js 14, TypeScript, Tailwind CSS, App Router |
| **Mobile** | Flutter 3.x, Dart |
| **Backend** | FastAPI, Python 3.14, uvicorn |
| **Primary LLM** | OpenRouter free tier (llama-3.3-70b, deepseek-v4-flash, gemma-4-31b) |
| **AI Runtime** | Google ADK — graceful fallback if not installed |
| **Fallback LLM** | Google Gemini (gemini-2.5-flash-lite -> gemini-2.0-flash) |
| **Auth** | JWT (PyJWT), SHA-256+salt password hashing |
| **Ingestion** | PyMuPDF (PDF), httpx (URL), csv.DictReader (CSV) |
| **Real Actions** | smtplib (Gmail SMTP), google-auth + gspread (Sheets), httpx (Slack) |
| **Storage** | JSON flat files (users.json, history.json, feedback.json) |
| **Development IDE** | Antigravity AI |

---

## Project Structure

```
insightflow/
+-- backend/
|   +-- main.py              # FastAPI app — 27 endpoints, CORS, auth middleware
|   +-- agents.py            # 5-agent system: Orion, Raven, Cipher, Resolver, Executor
|   +-- sdk_agents.py        # Alternative Google Gen AI SDK flow (flow_type=google_sdk)
|   +-- ingestion.py         # PDF, text, URL, CSV, feed source processors
|   +-- contradiction.py     # Credibility scoring, contradiction detection, noise filter
|   +-- constraints.py       # Pure Python constraint checker (zero API calls)
|   +-- simulator.py         # Action chain executor + real_actions integration
|   +-- real_actions.py      # Gmail SMTP, Google Sheets, Slack webhook
|   +-- auth.py              # JWT auth + SHA-256+salt + admin roles
|   +-- history_store.py     # Per-user analysis history (max 50 entries)
|   +-- feedback_store.py    # Domain feedback + learning context (last 15/domain)
|   +-- test_challenge1.py   # 80+ tests — Challenge 1 requirements CR1-CR8
|   +-- test_pipeline.py     # Integration tests: ingest -> analyze -> execute
|   +-- test_llm.py          # Model availability and fallback chain tests
|   +-- requirements.txt
|   +-- .env                 # API keys — NEVER commit
|
+-- frontend-next/
|   +-- src/
|       +-- app/
|       |   +-- page.tsx                     # Public landing page
|       |   +-- layout.tsx                   # Root layout + metadata
|       |   +-- (auth)/login / register
|       |   +-- (protected)/
|       |       +-- layout.tsx               # Auth guard + sidebar
|       |       +-- dashboard/page.tsx       # Main analysis interface
|       |       +-- analyze/page.tsx         # Step-wizard analysis + what-if
|       |       +-- history/page.tsx         # History list
|       |       +-- history/[id]/page.tsx    # History detail
|       |       +-- admin/page.tsx           # Admin panel
|       |       +-- settings/page.tsx        # Profile settings
|       +-- components/
|       |   +-- analysis/
|       |   |   +-- AgentDebate.tsx          # Agent insights + DisagreementMeter
|       |   |   +-- ActionChain.tsx          # 5-step chain with constraint badges
|       |   |   +-- FeedbackWidget.tsx       # Rating + learning feedback
|       |   |   +-- DisagreementMeter.tsx    # Agent consensus visualizer
|       |   |   +-- RiskTimeline.tsx         # Temporal contradiction timeline
|       |   +-- layout/ Sidebar.tsx Navbar.tsx
|       |   +-- ui/ Button Badge Card Input LoadingSpinner
|       +-- lib/
|       |   +-- api.ts                       # HTTP client — all 27 endpoints
|       |   +-- auth.ts                      # Token storage, auth state
|       +-- types/index.ts                   # TypeScript interfaces
|
+-- nexus_mobile/
|   +-- lib/
|       +-- main.dart                        # App entry, dark theme, auth gate
|       +-- config.dart                      # Base URL, timeouts
|       +-- models/  action_chain agent_result consensus execution_result source_analysis
|       +-- screens/
|       |   +-- login_screen.dart
|       |   +-- register_screen.dart
|       |   +-- input_screen.dart            # Ingestion + constraints + seeds + topic
|       |   +-- debate_screen.dart           # Credibility, temporal, contradictions, agents
|       |   +-- chain_screen.dart            # Action chain + execution log + baseline
|       |   +-- execution_screen.dart        # Real execution progress
|       |   +-- history_screen.dart
|       |   +-- history_detail_screen.dart   # Full detail + feedback widget
|       |   +-- settings_screen.dart
|       +-- services/
|           +-- api_service.dart             # HTTP client — all endpoints + constraints
|           +-- auth_service.dart            # JWT storage (SharedPreferences)
|
+-- README.md
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Flutter 3.x (for mobile)
- Gemini API key from [aistudio.google.com](https://aistudio.google.com/app/apikey)
- OpenRouter API key from [openrouter.ai/keys](https://openrouter.ai/keys) (free tier, recommended)

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:

```env
GOOGLE_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key

# Optional — Steps 2-4 fall back to simulation without these
SMTP_USER=your@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx
NOTIFY_EMAIL=recipient@example.com
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_SA_JSON={"type":"service_account",...}
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

```bash
uvicorn main:app --reload
# API:    http://localhost:8000
# Docs:   http://localhost:8000/docs
# Health: http://localhost:8000/health
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
static const String baseUrl = 'http://10.0.2.2:8000';   // Android emulator
// static const String baseUrl = 'http://192.168.x.x:8000'; // physical device
```

```bash
flutter run
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini API key (AI Studio) |
| `OPENROUTER_API_KEY` | Recommended | Primary LLM — free tier, reduces Gemini quota |
| `SMTP_USER` | Optional | Gmail address for stakeholder alerts |
| `SMTP_PASS` | Optional | Gmail App Password (16 chars, 2FA required) |
| `NOTIFY_EMAIL` | Optional | Recipient for Step 2 email alerts |
| `GOOGLE_SHEET_ID` | Optional | Sheet ID for Step 3 system state updates |
| `GOOGLE_SA_JSON` | Optional | Service account JSON as one line (newlines as `\n`) |
| `SLACK_WEBHOOK_URL` | Optional | Slack incoming webhook for Step 4 alerts |

---

## Live Test Results

**Run:** May 19 2026 — 3 sources (CSV + URL + Raw Text), no mock feed
**Constraints:** urgency=high, budget=PKR 600,000, staff=4, max_hours=6

### Ingestion

```
Sources processed : 3
Credibility map   : text=0.65  url=0.70  csv=1.00
Sources trusted   : 3  (none excluded)
Contradictions    : 1 detected
  TEXT vs CSV — "SKU-001 stock: 80 units" (text, May 18)
                contradicts "1200 units" (CSV, March 1)
  Trusted: TEXT — more recent Force Majeure notice dated May 18
Trend direction   : worsening
  SKU-001 stock: 1200 -> 600 -> 200 -> 80 units (March through May)
```

### Agent Debate

```
Orion  (Optimist)  confidence=85%
  40% Punjab supplier coverage prevents immediate halt of 3 production lines within 48h

Raven  (Pessimist) confidence=92%
  72-96h minimum delay severely underestimated — zero SKU-002 guarantees
  complete production shutdown within 14 days

Cipher (Realist)   confidence=92%
  90% probability production lines halt within 48h without intervention.
  SKU-001 at 80 units vs normal 1200. SKU-002 at absolute zero (Supplier-B).

Weighted confidence: 86.6%

Resolver:
  SKU-001 and SKU-002 experiencing severe disruption. High probability of
  complete shutdown within 14 days. Raven's zero-stock signal most critical.
  Swift global sourcing imperative to prevent irreversible business collapse.
```

### Action Chain (urgency=high, per-step limit: PKR 120k / 50min)

```
Step 1  MODIFIED  PKR  15,000   90min  Time 1.5h > 0.84h
  Verify SKU-001 and SKU-002 stock across all warehouses + Karachi/Port Qasim delays

Step 2  MODIFIED  PKR  10,000   60min  Time 1.0h > 0.84h
  Urgent report to exec team, production managers, procurement leads, logistics

Step 3  OK        PKR   8,000   45min
  Update ERP + IMS: zero SKU-002, flag SKU-001. Halt dependent production orders.

Step 4  MODIFIED  PKR 150,000  120min  Cost > PKR 120k AND time > 0.84h
  Global procurement: alternative suppliers + air cargo + bypass Sindh port routes

Step 5  OK        PKR  12,000   45min
  Daily crisis monitoring: supplier progress, air cargo, port recovery. 09:00 PST briefing.

TOTAL: PKR 195,000 / PKR 600,000 budget  |  3/5 steps flagged
```

### Real Integrations (from previous run)

```
Step 2  REAL EMAIL    -> zainabraza1960@gmail.com via Gmail SMTP
Step 3  REAL SHEET    -> Google Sheets (Service Account)
Step 4  REAL WEBHOOK  -> Slack workspace (HTTP 200)
Total latency: 25,547ms  |  Total cost: PKR 168,000
```

---

## Hackathon Checklist

- [x] Multi-source ingestion — PDF, text, CSV, URL, feed (5 types)
- [x] Credibility scoring — deterministic per-source scoring
- [x] Noise filtering — excluded sources below 0.30 threshold
- [x] Contradiction detection — cross-source conflicts with severity
- [x] Temporal trend analysis — improving / worsening / stable + rate-of-change
- [x] 5-agent parallel debate — Orion + Raven + Cipher via `asyncio.gather`
- [x] Resolver synthesis — single authoritative finding from 3 conflicting agents
- [x] Constraint validation — budget / time / staff / urgency (pure Python)
- [x] 5-step causal action chain — triggered_by + enables links
- [x] Real integrations — Gmail SMTP, Google Sheets, Slack Webhook
- [x] What-if counterfactual analysis — Executor re-run with modified constraints
- [x] Agent learning loop — feedback ratings injected as learning context per domain
- [x] Web frontend — Next.js 14 + TypeScript, App Router, dark theme
- [x] Mobile app — Flutter iOS/Android, full feature parity
- [x] JWT authentication — SHA-256+salt hashing, per-user history (max 50)
- [x] Admin panel — user management, feedback stats, domain breakdown
- [x] Google ADK integration — graceful fallback when not installed
- [x] OpenRouter as primary LLM — free tier, 4-model fallback chain
- [x] Robust JSON parser — `raw_decode()` handles prose-wrapped LLM responses
- [x] Rate-limit retry — 429 responses retried with backoff per model
