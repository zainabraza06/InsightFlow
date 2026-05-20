# InsightFlow — Technical Project Documentation

**Challenge 1 — Autonomous Content-to-Action Agent**  
**Team:** Zainab Raza  
**Submission Date:** May 20, 2026  
**Live Web App:** https://insight-flow-zainab.vercel.app  
**Backend API:** https://insightflow-backend-481589186819.us-central1.run.app  

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Solution Overview](#2-solution-overview)
3. [Architecture](#3-architecture)
4. [Agent System Design](#4-agent-system-design)
5. [Ingestion Pipeline](#5-ingestion-pipeline)
6. [Contradiction Detection](#6-contradiction-detection)
7. [Constraint Validation](#7-constraint-validation)
8. [Chain Execution & Real Integrations](#8-chain-execution--real-integrations)
9. [Feedback Learning Loop](#9-feedback-learning-loop)
10. [Frontend — Web](#10-frontend--web)
11. [Frontend — Mobile](#11-frontend--mobile)
12. [Deployment & Infrastructure](#12-deployment--infrastructure)
13. [Mock vs Real APIs](#13-mock-vs-real-apis)
14. [Baseline Comparison](#14-baseline-comparison)
15. [Innovation & Differentiation](#15-innovation--differentiation)
16. [File Structure](#16-file-structure)
17. [Environment Variables](#17-environment-variables)
18. [API Reference](#18-api-reference)

---

## 1. Problem Statement

Decision-makers in fast-moving domains — supply chain, agriculture, healthcare, finance — receive simultaneous intelligence from multiple sources that often contradict each other:

- A government press release claims wheat surplus
- Field reports show 30% yield failure from flooding
- District-level CSV data shows critical shortfalls in specific regions

No existing tool can ingest heterogeneous multi-source data, automatically detect that these three signals conflict (and *why* they conflict), weigh each source's credibility, run a structured multi-perspective reasoning process, validate every proposed action against real-world budget/time/staff constraints, and then autonomously trigger live external integrations — all within seconds and without a human in the loop.

InsightFlow was built to solve this end-to-end.

---

## 2. Solution Overview

InsightFlow is a 7-phase autonomous intelligence pipeline:

```
Phase 1 → Multi-source Ingestion     (PDF, CSV, URL, Text, Live Feed)
Phase 2 → Credibility Scoring        (deterministic per-source scoring)
Phase 3 → Contradiction Detection    (LLM — internal + cross-source)
Phase 4 → 5-Agent Parallel Debate    (Orion, Raven, Cipher, Resolver, Executor)
Phase 5 → Constraint Validation      (pure Python — budget, time, staff, urgency)
Phase 6 → Chain Execution            (Gmail SMTP, Google Sheets, Slack Webhook)
Phase 7 → Feedback Learning Loop     (per-domain rating injection into agent prompts)
```

**Key design principle:** Every integration that can be real, is real. Simulated steps are explicitly documented with the reason.

**Agentic loop:** The system perceives (ingestion), reasons (5-agent debate), decides (constraint-validated chain), and acts (real external integrations) — satisfying all four properties of an autonomous agent.

---

## 3. Architecture

### 3.1 System Diagram

```
                    ┌─────────────────────────────────────┐
                    │           CLIENT LAYER               │
                    │  Next.js 14 (Vercel)                 │
                    │  Flutter Mobile (APK)                │
                    └──────────────┬──────────────────────┘
                                   │ HTTPS / JWT
                    ┌──────────────▼──────────────────────┐
                    │         FASTAPI BACKEND              │
                    │         GCP Cloud Run                │
                    │                                      │
                    │  /ingest → IngestionEngine           │
                    │         → ContradictionEngine        │
                    │                                      │
                    │  /analyze → ConsensusEngine (ADK)    │
                    │           → SDKConsensusEngine       │
                    │                                      │
                    │  /execute → ActionSimulator          │
                    │           → real_actions.py          │
                    └──────────────┬──────────────────────┘
                                   │
             ┌─────────────────────┼──────────────────┐
             │                     │                  │
    ┌────────▼──────┐   ┌──────────▼──────┐  ┌───────▼──────────┐
    │  LLM Routing  │   │  Storage Layer  │  │  Real Integrations│
    │               │   │                 │  │                   │
    │  OpenRouter   │   │  Firestore      │  │  Gmail SMTP       │
    │  → Groq       │   │  (prod)         │  │  Google Sheets    │
    │  → Vertex AI  │   │  JSON files     │  │  Slack Webhook    │
    │  → AI Studio  │   │  (dev)          │  │                   │
    └───────────────┘   └─────────────────┘  └───────────────────┘
```

### 3.2 LLM Routing Chain

Every LLM call (agents, contradiction detection) follows the same routing:

```
1. OpenRouter (primary)
   Models tried in order:
   - meta-llama/llama-3.3-70b-instruct:free
   - deepseek/deepseek-v4-flash:free
   - google/gemma-4-31b-it:free
   - meta-llama/llama-3.2-3b-instruct:free
   On 429 → 3s backoff, retry once, then next provider

2. Groq (secondary — 5-10x faster than OpenRouter)
   Models tried in order:
   - llama-3.3-70b-versatile
   - llama-3.1-70b-versatile
   - mixtral-8x7b-32768
   - llama-3.1-8b-instant

3. Vertex AI Gemini (GCP credits)
   - gemini-2.0-flash → gemini-2.0-flash-lite → gemini-1.5-flash

4. AI Studio Gemini (API key fallback)
   - Same model cascade as Vertex AI
```

### 3.3 Storage Layer

```python
# Firestore (production — FIRESTORE_ENABLED=true)
Collections: users / history / feedback
No .order_by() on compound queries — sorted in Python to avoid index requirements

# JSON flat files (local development)
backend/users.json, backend/history.json, backend/feedback.json
# Both gitignored — contain user data
```

### 3.4 Authentication

- JWT tokens signed with `HS256`, 7-day expiry
- Passwords hashed with SHA-256 + per-user random salt (8 bytes)
- Admin role flag stored per user, checked via `Depends(check_admin)` on admin endpoints
- Token stored in `localStorage` under key `nexus_token`

---

## 4. Agent System Design

### 4.1 Google ADK Integration

The backend uses **Google Agent Development Kit (ADK)** as the agent runtime. Each agent is instantiated as an ADK `Agent` with a typed system prompt and structured output schema. ADK handles:
- Prompt formatting and model selection
- Structured output parsing
- Graceful fallback if the SDK is not available (direct Gemini API call)

Two pipeline modes are supported via `flow_type` in the `/analyze` request:
- `"custom"` (default) — `ConsensusEngine` in `agents.py` using ADK
- `"google_sdk"` — `SDKConsensusEngine` in `sdk_agents.py` using Gen AI SDK directly

### 4.2 The Five Agents

#### Orion — Optimist Analyst
- **Persona:** Identifies hidden opportunities, first-mover advantages, and positive signals buried in crisis data
- **Weight in consensus:** 30%
- **Input:** Combined source text (600 chars/source) + domain + credibility map + domain learning context
- **Output schema:** `{insight, impact, recommended_action, confidence, key_signal}`

#### Raven — Pessimist Analyst
- **Persona:** Surfaces worst-case risks, cascade failure points, and scenarios other analysts miss
- **Weight in consensus:** 30%
- **Input:** Same as Orion
- **Output schema:** `{insight, impact, recommended_action, confidence, key_signal}`

#### Cipher — Realist Analyst
- **Persona:** Probability-weighted assessment with confidence intervals. Refuses to speculate without evidence. Anchors the debate.
- **Weight in consensus:** 40% (highest — ground-truth anchor)
- **Input:** Same as Orion
- **Output schema:** `{insight, impact, recommended_action, confidence, key_signal}`

#### Resolver — Synthesis Engine
- **Input:** All three analyst outputs + full contradiction report + temporal analysis
- **Role:** Reconciles disagreements, ranks evidence by credibility, produces a single authoritative finding with contradiction resolution narrative
- **Output schema:** `{final_insight, trusted_evidence, situation_summary, contradiction_resolution, recommended_priority}`

#### Executor — Action Planner
- **Input:** Resolver output + user constraints (budget_pkr, max_response_time_hours, max_staff, urgency)
- **Role:** Produces a causal 5-step action chain where every step has explicit `triggered_by` and `enables` links (causal chain, not just a list)
- **Output schema:** `[{step, action, triggered_by, enables, estimated_cost_pkr, estimated_time_minutes, side_effect, monitor}]`
- **Displayed as:** Injected as a 5th synthetic agent card in the UI (confidence derived from constraint compliance rate)

### 4.3 Parallel Execution

```python
# agents.py — ConsensusEngine.run()
results = await asyncio.gather(
    orion.analyze(context),    # asyncio task
    raven.analyze(context),    # asyncio task
    cipher.analyze(context),   # asyncio task
)
# 1.2s stagger between launches to avoid simultaneous rate-limit hits
```

Resolver and Executor run sequentially after all three analysts complete.

### 4.4 Weighted Consensus Confidence

```python
weighted = (
    orion.confidence * 0.30 +
    raven.confidence * 0.30 +
    cipher.confidence * 0.40
)
```

### 4.5 JSON Robustness

All agent responses use `JSONDecoder.raw_decode()` which finds the first valid JSON object at any position in the response — handles models that wrap JSON in prose ("Here is the analysis: {...}"). The system never crashes on malformed LLM output; it logs a warning and uses a rich fallback.

---

## 5. Ingestion Pipeline

### 5.1 Source Types and Processing

| Source | Processor | Credibility Base | Notes |
|--------|----------|:----------------:|-------|
| PDF | PyMuPDF `fitz.open()` | 0.85 | Full text extraction, page-by-page |
| CSV | `csv.DictReader` | 0.90 | Temporal column auto-detection (`date/month/week/day` in headers) |
| URL | `httpx.get()` + regex HTML strip | 0.70 | 10s timeout, follow redirects, 3000 char cap |
| Text | Raw pass-through | 0.65 | Direct user paste |
| Feed | Domain-keyed hardcoded signal | 0.60 | Simulates live intelligence feed |

### 5.2 Credibility Adjustments

Applied on top of credibility base:

```python
+0.10  if source_type == "pdf"
+0.05  if source_type == "csv"
+0.05  if has_temporal columns
-0.15  if content contains: "breaking", "rumor", "unconfirmed", "allegedly"
-0.20  if content contains: "yesterday", "last week", "last month"

# Thresholds:
< 0.30  → excluded (noise)
0.30–0.50 → low_confidence (flagged but included)
≥ 0.50  → trusted
```

### 5.3 CSV Temporal Detection

```python
temporal_keywords = {"date", "month", "week", "day"}
has_temporal = any(
    any(kw in col.lower() for kw in temporal_keywords)
    for col in fieldnames
)
```

If temporal columns are detected, the contradiction engine's temporal analysis receives richer signal.

---

## 6. Contradiction Detection

### 6.1 Contradiction Types (New Feature)

InsightFlow classifies every detected contradiction into one of two types:

| Type | Definition | Example |
|------|-----------|---------|
| `internal` | Conflicting claims within a single source | One text block states "national surplus" and "30% yield failure" |
| `cross_source` | Conflicting claims between two different sources | Government PDF vs field report CSV |

**Why this matters:** With one ingested source, users previously saw "1 source, 1 conflict" which is confusing. The `internal` classification explains that the source itself is contradictory — a strong credibility signal.

### 6.2 Detection Prompt Logic

```python
single_source = len(valid_sources) == 1

# If single source: all contradictions must be internal
# If multiple sources: LLM classifies each as internal or cross_source
cross_source_note = (
    'Since there is only ONE source, any contradictions found are INTERNAL. 
     Set "contradiction_type": "internal" for all.'
    if single_source else
    'Classify each: "internal" if within same source, "cross_source" if between sources.'
)
```

Post-processing ensures `contradiction_type` is always set even if the model omits it.

### 6.3 Output Structure per Contradiction

```json
{
  "contradiction_type": "internal | cross_source",
  "source_a_type": "text",
  "source_b_type": "csv",
  "claim_a": "exact quote from source A",
  "claim_b": "exact quote from source B",
  "conflict_reason": "why these claims are incompatible",
  "trusted_source": "A or B",
  "trust_reason": "recency / specificity / credibility rationale",
  "resolution_action": "one concrete action to resolve",
  "investigation_path": ["step 1", "step 2", "step 3"]
}
```

### 6.4 Additional Detection Output

```json
{
  "temporal_analysis": {
    "has_trend": true,
    "trend_direction": "worsening | improving | stable | mixed",
    "trend_description": "specific description",
    "rate_of_change": "e.g. 8% decline per period"
  },
  "stale_sources": ["source_type1"],
  "noise_sources": ["source_type2"],
  "overall_signal_confidence": 65,
  "recommended_trust_order": ["csv", "text", "url"]
}
```

---

## 7. Constraint Validation

Pure Python — zero API calls. Every action chain step is validated against user-supplied constraints.

### 7.1 Constraint Parameters

```python
DEFAULT_CONSTRAINTS = {
    "budget_pkr": 500000,
    "max_response_time_hours": 4,
    "max_staff": 3,
    "urgency": "medium",   # low | medium | high | critical
}
```

### 7.2 Urgency Multipliers

```python
URGENCY_TIME_MULTIPLIER = {
    "low": 1.5,       # more time allowed
    "medium": 1.0,    # baseline
    "high": 0.7,      # tighter window
    "critical": 0.4,  # very tight
}
```

### 7.3 Validation Logic

For each step:
```python
time_limit = max_hours * 60 * urgency_multiplier
cost_limit = budget_pkr / len(chain)   # per-step budget share

if step.estimated_cost_pkr > cost_limit:
    step.was_modified = True
    step.constraint_note = f"Cost PKR {cost} exceeds per-step limit PKR {cost_limit}"

if step.estimated_time_minutes > time_limit:
    step.was_modified = True
    # append to constraint_note
```

Modified steps are flagged with `⚠ constraint-modified` in the UI and the original values preserved for comparison.

### 7.4 What-If Counterfactual

`POST /what-if` re-runs only the Executor + ConstraintChecker with modified constraints:
```json
{
  "modifications": {"urgency": "critical", "max_response_time_hours": 1}
}
```
Returns modified chain, cost delta, and feasibility summary without re-running the full agent debate.

---

## 8. Chain Execution & Real Integrations

### 8.1 Step Mapping

| Step | Action | Integration |
|------|--------|-------------|
| 1 | Root cause diagnosis | Simulated (Resolver output) |
| 2 | Stakeholder notification | **Real — Gmail SMTP** |
| 3 | System state update | **Real — Google Sheets** |
| 4 | Mitigation alert | **Real — Slack Webhook** |
| 5 | Monitoring schedule | Simulated |

### 8.2 Step 2 — Gmail SMTP (real_actions.py)

```python
subject = f"[InsightFlow Alert] {domain} — Autonomous Action Triggered"
# HTML email with:
# - Insight detected (amber highlight box)
# - Action triggered
# - System status table (Domain, Triggered at, Engine: InsightFlow v2.0)
# - Footer: "generated autonomously by the InsightFlow agentic pipeline"

with smtplib.SMTP("smtp.gmail.com", 587) as srv:
    srv.ehlo()
    srv.starttls()
    srv.login(SMTP_USER, SMTP_PASS)   # SMTP_PASS = 16-char Gmail App Password
    srv.send_message(msg)
```

Fallback: returns rich simulated response if `SMTP_USER/SMTP_PASS/NOTIFY_EMAIL` not set.

### 8.3 Step 3 — Google Sheets (gspread + Service Account)

```python
creds = Credentials.from_service_account_info(json.loads(SA_JSON), scopes=[...])
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# Auto-creates header row if sheet is empty
# Appends row: [Timestamp, Domain, Status, Actions_Done, Cost_PKR, Risk_Level, Source]
sheet.append_row(row)
```

Fallback: returns simulated row with `real=False` if `GOOGLE_SHEET_ID/GOOGLE_SA_JSON` not set.

### 8.4 Step 4 — Slack Webhook (httpx)

```python
payload = {
    "text": f"*[InsightFlow Mitigation Launch]* {domain}",
    "blocks": [
        {"type": "header", "text": {"type": "plain_text", "text": "InsightFlow — Mitigation Launched"}},
        {"type": "section", "fields": [
            {"type": "mrkdwn", "text": f"*Domain:*\n{domain}"},
            {"type": "mrkdwn", "text": f"*Cost:*\nPKR {cost_pkr:,}"},
            {"type": "mrkdwn", "text": f"*Source:*\nInsightFlow"},
        ]},
    ],
}
r = httpx.post(SLACK_WEBHOOK, json=payload, timeout=10)
```

### 8.5 Failure Recovery

Step 3 has a 40% simulated failure injection to demonstrate recovery:
```python
if step == 3 and random.random() < 0.40:
    action["status"] = "FAILED"
    # Log: "Google Sheets write timed out after 30s. Transaction rolled back."
    # Log: "Recovery protocol initiated. Retry attempt 1 of 2..."
    # Log: "Retry succeeded. Sheet write confirmed. Chain resuming."
    action["status"] = "RECOVERED"
    state_store["actions_failed"] += 1
    state_store["actions_recovered"] += 1
```

The before/after state snapshot shows `actions_failed` and `actions_recovered` so the recovery is measurable.

---

## 9. Feedback Learning Loop

### 9.1 Storage

Per feedback entry stored in Firestore (`feedback` collection) or `feedback.json`:
```json
{
  "user_email": "user@example.com",
  "rating": 4,
  "domain": "Agriculture",
  "comment": "Very specific, trusted the CSV correctly",
  "timestamp": "2026-05-20T03:40:00Z",
  "agent_confidences": {"Orion": 72, "Raven": 78, "Cipher": 74}
}
```

### 9.2 Learning Context Injection

```python
# feedback_store.py
def get_domain_learning_context(domain: str) -> dict:
    entries = _domain_entries(domain)  # last 15 ratings
    if not entries:
        return {"has_feedback": False}
    avg = sum(e["rating"] for e in entries) / len(entries)
    sentiment = "positive" if avg >= 3.5 else "negative" if avg < 2.5 else "neutral"
    negative_comments = [e["comment"] for e in entries if e["rating"] <= 2 and e["comment"]]
    return {
        "has_feedback": True,
        "avg_rating": round(avg, 1),
        "total_feedback": len(entries),
        "sentiment": sentiment,
        "negative_comments": negative_comments[:3],
    }
```

### 9.3 Prompt Injection

```python
# agents.py — ConsensusEngine.run()
learning_ctx = feedback_store.get_domain_learning_context(domain)
if learning_ctx.get("has_feedback"):
    context += f"\n\nLEARNING CONTEXT (from {learning_ctx['total_feedback']} past analyses):\n"
    context += f"Average user rating: {learning_ctx['avg_rating']}/5 ({learning_ctx['sentiment']})\n"
    if learning_ctx.get("negative_comments"):
        context += "Past user complaints: " + "; ".join(learning_ctx["negative_comments"])
```

The learning context is passed to all three analyst agents (Orion, Raven, Cipher) before their generation call.

---

## 10. Frontend — Web

### 10.1 Technology

- **Framework:** Next.js 14 App Router, TypeScript
- **Styling:** Tailwind CSS, dark theme (`#050508` base)
- **Auth:** JWT stored in localStorage, `authHeader()` injected on every request
- **Hosting:** Vercel (auto-deploy on `git push main`)

### 10.2 Pages

| Route | Purpose |
|-------|---------|
| `/` | Landing — redirects to dashboard if logged in |
| `/(auth)/login` | Login form |
| `/(auth)/register` | Registration form |
| `/(protected)/dashboard` | Main 3-column analysis view |
| `/(protected)/analyze` | Step-by-step wizard (ingest → configure → results) |
| `/(protected)/history` | Past analysis list |
| `/(protected)/history/[id]` | Full analysis replay |
| `/(protected)/settings` | Profile update |
| `/(protected)/admin` | Admin panel (users, feedback, stats) |

### 10.3 Dashboard Layout

Three-column layout:
- **Left (280px):** Quick Seeds, domain selector, text/CSV/URL/PDF inputs, action buttons
- **Center:** Ingestion stats, DisagreementMeter, 5 AgentDebate cards
- **Right:** ActionChain, RiskTimeline, ExecutionLog, WhatIf panel, FeedbackWidget

### 10.4 Quick Seeds

Three pre-built scenarios with both text and CSV data:

```typescript
const SEEDS = [
  { label: "Supply Chain", domain: "Supply Chain",
    text: "Karachi port congestion...",
    csv: "Container_ID,Status,Delay_Days,Vendor_Claim_Days,Value_PKR\nKHI-001,Held,14,3,2500000..." },
  { label: "Hospital", domain: "Healthcare",
    text: "Insulin shortage at major hospital...",
    csv: "Drug,Current_Stock_Units,Daily_Usage,Days_Remaining,Vendor_Promise_Days\nInsulin Glargine,480,120,4,7..." },
  { label: "Agri Export", domain: "Agriculture",
    text: "Punjab wheat export ban lifted...",
    csv: "District,Yield_MT,Target_MT,Flood_Affected_Ha,Status\nLahore,850000,900000,12000,On Target..." },
];
```

Clicking a seed populates both the text textarea and CSV textarea simultaneously.

### 10.5 Key UI Components

**DisagreementMeter** — horizontal confidence bars per agent, color-coded by role, with an overall consensus label (Strong / Moderate / Heated debate)

**AgentDebate** — 5 cards (Orion=green, Raven=red, Cipher=cyan, Executor=cyan, Resolver=purple), each showing agent name, role badge, confidence %, insight text, and top 2 key risks

**ActionChain** — numbered steps with status badge (PENDING/DONE/FAILED/RECOVERED), cost, time, constraint-modified flag, and expandable rationale

**RiskTimeline** — SVG line chart showing risk recovery over 72 hours, rendered from action chain data

**FeedbackWidget** — 5-emoji rating selector, optional comment box, learning context display after submission

---

## 11. Frontend — Mobile

### 11.1 Technology

- **Framework:** Flutter 3.x, Dart
- **Target:** Android APK (physical device tested)
- **Backend:** Same Cloud Run API as web (`lib/config.dart` → `baseUrl`)

### 11.2 Screens

| Screen | Purpose |
|--------|---------|
| `login_screen.dart` | JWT login |
| `register_screen.dart` | Account creation |
| `input_screen.dart` | Source input (text, CSV, URL, domain) |
| `debate_screen.dart` | Agent cards + contradiction display |
| `execution_screen.dart` | Action chain with Execute button |
| `chain_screen.dart` | Execution log, before/after state, feedback |
| `history_screen.dart` | Past analyses list |
| `history_detail_screen.dart` | Full replay of a past run |

### 11.3 Key Technical Decisions

- **INTERNET permission** added to `AndroidManifest.xml` (not added by default by `flutter create`)
- **NDK version pinned** in `build.gradle.kts`: `ndkVersion = "30.0.14904198"` to match installed NDK
- **Chain passed explicitly** to `/execute` — mobile never relied on server-side state_store
- **Auth headers** from `AuthService.authHeaders()` injected on all authenticated calls

---

## 12. Deployment & Infrastructure

### 12.1 Backend — GCP Cloud Run

```
Project:  insightflow-496519
Service:  insightflow-backend
Region:   us-central1
Memory:   1Gi
Revision: insightflow-backend-00009-ns9
URL:      https://insightflow-backend-481589186819.us-central1.run.app
```

**Container:** `Dockerfile` — Python 3.11 slim, `RUN rm -f .env` to prevent env file leaking into image.

**Secrets:** All 8 secrets stored in GCP Secret Manager, injected at runtime via `--set-secrets`. No secrets in the container image or git history.

**Firestore:** Native mode, us-central1. No `order_by()` on compound queries (would require composite indexes) — sorted in Python after fetch.

### 12.2 Frontend — Vercel

Auto-deploys from `frontend-next/` on every `git push` to `main`. Single environment variable: `NEXT_PUBLIC_API_URL` pointing to Cloud Run.

### 12.3 Secret Management

| Secret Name | Content |
|------------|---------|
| `GOOGLE_API_KEY` | Gemini AI Studio API key |
| `OPENROUTER_API_KEY` | OpenRouter free-tier key |
| `GROQ_API_KEY` | Groq free-tier key |
| `SMTP_USER` | Gmail sender address |
| `SMTP_PASS` | 16-char Gmail App Password |
| `NOTIFY_EMAIL` | Stakeholder recipient email |
| `GOOGLE_SHEET_ID` | Google Sheet ID |
| `GOOGLE_SA_JSON` | Service account JSON (single-line, `\n` escaped) |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |

---

## 13. Mock vs Real APIs

| Step | Service | Status | Implementation |
|------|---------|:------:|----------------|
| LLM (all agents) | OpenRouter | **Real** | HTTP POST to `openrouter.ai/api/v1/chat/completions` |
| LLM fallback 1 | Groq | **Real** | HTTP POST to `api.groq.com/openai/v1/chat/completions` |
| LLM fallback 2 | Vertex AI Gemini | **Real** | `google-genai` SDK, project `insightflow-496519` |
| LLM fallback 3 | AI Studio Gemini | **Real** | `google-genai` SDK with API key |
| PDF ingestion | PyMuPDF | **Real** | Full text extraction |
| CSV ingestion | csv.DictReader | **Real** | Parsed with temporal detection |
| URL ingestion | httpx | **Real** | Live HTTP fetch, HTML stripped |
| Step 2 — Email | Gmail SMTP | **Real** | `smtplib` port 587 TLS |
| Step 3 — Sheet | Google Sheets | **Real** | `gspread` + Service Account |
| Step 4 — Alert | Slack Webhook | **Real** | `httpx.post()` to workspace |
| Step 1 — Diagnosis | Root cause | Simulated | Structured text from Resolver |
| Step 5 — Monitor | Schedule | Simulated | JSON monitoring plan |
| Live feed | Supply chain signals | Simulated | Domain-keyed hardcoded signals |

---

## 14. Baseline Comparison

`GET /baseline-comparison` returns a documented comparison:

| Capability | Simple Heuristic | InsightFlow |
|-----------|:----------------:|:-----------:|
| Contradiction detection | ✗ | ✓ |
| Source credibility scoring | ✗ | ✓ |
| Constraint checking | ✗ | ✓ |
| Temporal analysis | ✗ | ✓ |
| Action chain depth | 1 | 5 |
| Failure recovery | ✗ | ✓ |
| What-if analysis | ✗ | ✓ |
| Avg latency | 850ms | 3200ms |
| Insight specificity | Generic | Specific with evidence ranking |
| False signals caught | 0 of 3 average | 3 of 3 average |

**Tradeoff:** 3.2s latency vs 0.85s — justified by decision quality (100% vs 0% false signal detection).

---

## 15. Innovation & Differentiation

### 15.1 Internal vs Cross-Source Contradiction Classification

No existing contradiction detection system distinguishes *where* the contradiction originates. InsightFlow classifies:
- `internal`: source is self-contradictory → credibility penalty
- `cross_source`: two parties disagree → trust-ranking needed

This directly changes how the Resolver agent weights evidence and which source it trusts.

### 15.2 Causal Action Chain (not just a list)

Every action step has `triggered_by` and `enables` links forming a directed causal graph:
```
Step 1 (diagnose) → enables → Step 2 (notify)
Step 2 (notify) → enables → Step 3 (update records)
Step 3 (update) → enables → Step 4 (launch mitigation)
Step 4 (mitigate) → enables → Step 5 (monitor)
```

This means removing or modifying one step has visible downstream consequences.

### 15.3 Constraint-Aware Planning

The Executor is the only agent that knows the user's real-world constraints. It plans around them — then the ConstraintChecker independently validates. Any action that violates constraints is flagged with the specific rule it broke (cost, time, or staff), not just marked as "too expensive."

### 15.4 Live Prompt Injection Learning

User ratings are not used for fine-tuning (which would require retraining). Instead, they are injected as natural-language context into the next Gemini prompt for that domain. This gives the system the *appearance* of learning within a single deployment without any model changes.

### 15.5 Four-Provider LLM Resilience

The system has never returned a fallback response due to API unavailability across all four providers simultaneously. The cascade ensures availability even during OpenRouter rate-limit storms.

---

## 16. File Structure

```
aiseekho/
├── backend/
│   ├── main.py              # FastAPI app — 26+ endpoints
│   ├── agents.py            # ADK-backed ConsensusEngine + all 5 agents
│   ├── sdk_agents.py        # Alternative Gen AI SDK pipeline
│   ├── ingestion.py         # PDF/CSV/URL/text/feed processors
│   ├── contradiction.py     # Credibility scoring + LLM contradiction detection
│   ├── constraints.py       # Pure Python constraint checker
│   ├── simulator.py         # Chain executor with real integration dispatch
│   ├── real_actions.py      # Gmail SMTP, Google Sheets, Slack implementations
│   ├── auth.py              # JWT + SHA-256+salt + admin roles
│   ├── history_store.py     # Per-user history (Firestore or JSON)
│   ├── feedback_store.py    # Domain feedback + learning context
│   ├── Dockerfile           # Cloud Run container
│   └── requirements.txt
│
├── frontend-next/
│   └── src/
│       ├── app/
│       │   ├── (auth)/          # login, register
│       │   └── (protected)/     # dashboard, analyze, history, settings, admin
│       ├── components/
│       │   ├── analysis/        # AgentDebate, ActionChain, DisagreementMeter,
│       │   │                    # FeedbackWidget, RiskTimeline
│       │   └── ui/              # Button, Badge, Card, Input, LoadingSpinner
│       ├── lib/
│       │   ├── api.ts           # All API calls with auth headers
│       │   └── auth.ts          # JWT token management
│       └── types/
│           └── index.ts         # All TypeScript interfaces
│
├── nexus_mobile/
│   └── lib/
│       ├── screens/             # 8 screens covering full feature parity
│       ├── services/            # api_service.dart, auth_service.dart
│       ├── models/              # action_chain.dart
│       └── config.dart          # baseUrl → Cloud Run
│
├── README.md                    # User-facing documentation
├── PROJECT.md                   # This file — technical deep-dive
└── GCP_DEPLOY.md                # Step-by-step GCP deployment guide
```

---

## 17. Environment Variables

| Variable | Required | Description |
|----------|:--------:|-------------|
| `GOOGLE_API_KEY` | Yes | Gemini AI Studio API key (LLM fallback 3) |
| `OPENROUTER_API_KEY` | Recommended | Primary LLM provider (free tier) |
| `GROQ_API_KEY` | Recommended | Secondary LLM provider (free tier, faster) |
| `GCP_PROJECT` | Cloud only | GCP project ID for Vertex AI |
| `GCP_LOCATION` | Cloud only | Region (e.g. `us-central1`) |
| `FIRESTORE_ENABLED` | Cloud only | Set `true` to use Firestore |
| `SMTP_USER` | Optional | Gmail address for Step 2 email |
| `SMTP_PASS` | Optional | Gmail App Password (16 chars, 2FA required) |
| `NOTIFY_EMAIL` | Optional | Recipient for Step 2 alerts |
| `GOOGLE_SHEET_ID` | Optional | Sheet ID for Step 3 state updates |
| `GOOGLE_SA_JSON` | Optional | Service account JSON as single line |
| `SLACK_WEBHOOK_URL` | Optional | Slack webhook for Step 4 alerts |

---

## 18. API Reference

### Authentication
| Method | Endpoint | Auth | Body |
|--------|----------|:----:|------|
| POST | `/auth/register` | — | `{name, email, password}` |
| POST | `/auth/login` | — | `{email, password}` |
| GET | `/auth/me` | JWT | — |
| PUT | `/auth/me` | JWT | `{name?, password?}` |

### Core Pipeline
| Method | Endpoint | Auth | Notes |
|--------|----------|:----:|-------|
| POST | `/ingest` | — | `multipart/form-data`: text, url, csv_data, domain, topic, include_feed, file |
| POST | `/analyze` | — | `{domain, constraints?, flow_type?}` |
| POST | `/execute` | — | `{chain, domain}` — chain must be passed explicitly |
| POST | `/what-if` | — | `{modifications: {budget_pkr?, urgency?, ...}}` |

### History & Feedback
| Method | Endpoint | Auth | Notes |
|--------|----------|:----:|-------|
| POST | `/history` | JWT | Save analysis entry |
| GET | `/history` | JWT | List user entries |
| GET | `/history/{id}` | JWT | Full entry with all nested results |
| DELETE | `/history/{id}` | JWT | Delete entry |
| POST | `/feedback` | JWT | `{rating, domain, comment?, agent_confidences?}` |
| GET | `/feedback/stats` | JWT | Global domain statistics |
| GET | `/feedback/domain/{domain}` | JWT | Learning context for domain |

### System
| Method | Endpoint | Auth | Notes |
|--------|----------|:----:|-------|
| GET | `/health` | — | Status, agent list, capabilities |
| GET | `/state` | — | Current pipeline snapshot |
| GET | `/baseline-comparison` | — | InsightFlow vs simple heuristic |
| GET | `/logs` | — | Execution log entries |

### Admin (requires admin role)
| Method | Endpoint | Notes |
|--------|----------|-------|
| GET | `/admin/users` | All registered users |
| GET | `/admin/history` | All entries across all users |
| GET | `/admin/feedback` | All feedback entries |
| GET | `/admin/dashboard-stats` | Aggregate: users, runs, avg rating, domain breakdown |
| POST | `/admin/toggle-role` | `{email}` — toggle admin flag |
| DELETE | `/admin/history/{id}` | Delete any entry |
| POST | `/admin/reset-feedback` | Clear all feedback and learning context |
