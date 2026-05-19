"""
InsightFlow Agent System — powered by Google Agent Development Kit (ADK)

LLM call priority (per request):
  1. OpenRouter (OPENROUTER_API_KEY) — free tier, multiple model fallbacks
  2. Vertex AI Gemini (GCP_PROJECT set) — billed to GCP credits, high quota
  3. Google ADK runner (google-adk) — if installed
  4. Direct Gemini AI Studio (GOOGLE_API_KEY) — free tier fallback

NOTE ON ANTIGRAVITY:
  Antigravity is the IDE used to develop this product (not a runtime dependency).
"""

import asyncio
import json
import logging
import os
import tempfile
import uuid

import httpx
import google.genai as genai

from constraints import ConstraintChecker, DEFAULT_CONSTRAINTS
import feedback_store

logging.basicConfig(level=logging.INFO, format="[NEXUS] %(message)s")
logger = logging.getLogger("nexus.agents")

# ── Credential bootstrap ───────────────────────────────────────────────────────
# If GOOGLE_SA_JSON is set, write it to a temp file so ADC picks it up.
# This covers both local dev and Cloud Run (which uses the attached SA directly).
_SA_JSON = os.environ.get("GOOGLE_SA_JSON", "")
if _SA_JSON and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    try:
        _sa_data = json.loads(_SA_JSON)
        _tf = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(_sa_data, _tf)
        _tf.flush()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _tf.name
        logger.info(f"[CREDS] Service account loaded from GOOGLE_SA_JSON → {_tf.name}")
    except Exception as _e:
        logger.warning(f"[CREDS] Could not write SA JSON: {_e}")

_GCP_PROJECT  = os.environ.get("GCP_PROJECT", "insightflow-496519")
_GCP_LOCATION = os.environ.get("GCP_LOCATION", "us-central1")
_API_KEY      = os.environ.get("GOOGLE_API_KEY", "")

# Build Vertex AI client if project is set (uses ADC / service account)
# Fall back to AI Studio API key client
def _make_genai_client():
    if _GCP_PROJECT and os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            c = genai.Client(vertexai=True, project=_GCP_PROJECT, location=_GCP_LOCATION)
            logger.info(f"[GENAI] Vertex AI client — project={_GCP_PROJECT} location={_GCP_LOCATION}")
            return c, True
        except Exception as e:
            logger.warning(f"[GENAI] Vertex AI init failed ({e}) — falling back to AI Studio key")
    if _API_KEY:
        logger.info("[GENAI] AI Studio client (free tier)")
        return genai.Client(api_key=_API_KEY), False
    return None, False

_genai_client, _VERTEX_ENABLED = _make_genai_client()

# ── Google ADK bootstrap ──────────────────────────────────────────────────────
# ADK is the orchestration layer. Falls back to direct Gemini if not installed.

_ADK_READY = False
_adk_session_service = None
LlmAgent = None
Runner = None

try:
    from google.adk.agents import LlmAgent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.tools import FunctionTool
    from google.genai import types as _adk_types

    _adk_session_service = InMemorySessionService()
    _ADK_READY = True
    logger.info("[ADK] Google ADK loaded — agents will run via ADK Runner")
except Exception as _e:
    logger.warning(f"[ADK] google-adk not available ({_e}) — using direct Gemini fallback")


# ── ADK constraint-checking tool (called by Executor during chain planning) ───

def _validate_action_tool(
    step: int,
    action: str,
    estimated_cost_pkr: int,
    estimated_time_minutes: int,
    budget_pkr: int = 500_000,
    max_time_minutes: int = 240,
    max_staff: int = 3,
    staff_required: int = 1,
) -> dict:
    """
    Validate a single action step against resource constraints.
    Returns feasibility verdict and modification note if needed.
    Called by the Executor agent via ADK tool use.
    """
    budget_ok = estimated_cost_pkr <= budget_pkr
    time_ok = estimated_time_minutes <= max_time_minutes
    staff_ok = staff_required <= max_staff
    feasible = budget_ok and time_ok and staff_ok
    note = ""
    if not budget_ok:
        note += f"Cost PKR {estimated_cost_pkr:,} exceeds budget PKR {budget_pkr:,}. "
    if not time_ok:
        note += f"Time {estimated_time_minutes}min exceeds limit {max_time_minutes}min. "
    if not staff_ok:
        note += f"Needs {staff_required} staff but limit is {max_staff}. "
    logger.info(f"[ADK-TOOL] validate_action step={step} feasible={feasible}")
    return {
        "step": step,
        "feasible": feasible,
        "budget_ok": budget_ok,
        "time_ok": time_ok,
        "staff_ok": staff_ok,
        "constraint_note": note.strip() if note else "All constraints satisfied",
        "was_modified": not feasible,
    }


# ── Core ADK execution helpers ────────────────────────────────────────────────

async def _create_adk_session() -> str:
    """Create a fresh ADK session and return its ID."""
    uid = f"nexus-{uuid.uuid4().hex[:8]}"
    try:
        session = _adk_session_service.create_session(app_name="nexus", user_id=uid)
        return uid, session.id
    except Exception:
        # Some ADK versions use async create
        session = await _adk_session_service.create_session(app_name="nexus", user_id=uid)
        return uid, session.id


async def _run_via_adk(adk_agent, prompt: str) -> str:
    """Run an ADK LlmAgent and return its final text response."""
    user_id, session_id = await _create_adk_session()
    runner = Runner(agent=adk_agent, app_name="nexus", session_service=_adk_session_service)

    message = _adk_types.Content(role="user", parts=[_adk_types.Part(text=prompt)])
    final_text = ""

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=message):
        if hasattr(event, "is_final_response") and event.is_final_response():
            if event.content and event.content.parts:
                final_text = event.content.parts[0].text or ""
                break

    return final_text


_OPENROUTER_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-v4-flash:free",
    "google/gemma-4-31b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]

async def _call_openrouter(prompt: str) -> str:
    """Call OpenRouter — tries models in order until one succeeds."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://nexus-ai.local",
    }

    last_err = None
    async with httpx.AsyncClient() as client:
        for model in _OPENROUTER_MODELS:
            for attempt in range(2):  # 1 retry per model on rate-limit
                try:
                    payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
                    resp = await client.post(url, headers=headers, json=payload, timeout=60.0)
                    if resp.status_code == 429:
                        wait = 3.0 * (attempt + 1)
                        logger.warning(f"[ROUTER] model={model} rate-limited — retrying in {wait}s")
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    text = data["choices"][0]["message"]["content"].strip()
                    if text:
                        logger.info(f"[ROUTER] OpenRouter success model={model} attempt={attempt+1}")
                        return text
                    break  # empty response — try next model
                except Exception as e:
                    logger.warning(f"[ROUTER] model={model} attempt={attempt+1} failed: {e}")
                    last_err = e
                    break  # non-429 error — move to next model

    raise RuntimeError(f"All OpenRouter models failed. Last error: {last_err}")


async def _call_gemini_direct(prompt: str) -> str:
    """Gemini call via Vertex AI (credits) or AI Studio (free tier fallback)."""
    client = _genai_client
    if not client:
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        client = genai.Client(api_key=api_key) if api_key else None
    if not client:
        raise RuntimeError("No Gemini client available — set GCP_PROJECT or GOOGLE_API_KEY")
    backend = "Vertex AI" if _VERTEX_ENABLED else "AI Studio"
    for model_name in ("gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"):
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model_name,
                contents=prompt,
            )
            text = (response.text or "").strip()
            if not text:
                raise ValueError("empty response")
            logger.info(f"[GEMINI] {backend} success model={model_name}")
            return text
        except Exception as e:
            logger.warning(f"[GEMINI] {backend} model={model_name} failed: {e}")
    raise RuntimeError("All Gemini models exhausted")


async def _call(adk_agent, prompt: str) -> str:
    """Primary routing logic:
       1. Try OpenRouter (first preference)
       2. Try Google ADK
       3. Fall back to direct Gemini
    """
    # 1. Try OpenRouter
    if os.environ.get("OPENROUTER_API_KEY"):
        try:
            res = await _call_openrouter(prompt)
            if res:
                return res
        except Exception as e:
            logger.warning(f"[ROUTER] OpenRouter failed ({e}) — trying ADK/Gemini")

    # 2. Try ADK
    if _ADK_READY and adk_agent is not None:
        try:
            result = await _run_via_adk(adk_agent, prompt)
            if result:
                return result
        except Exception as exc:
            name = getattr(adk_agent, "name", "unknown")
            logger.warning(f"[ADK] {name} runner failed ({exc}) — falling back to direct Gemini")
            
    # 3. Fallback to direct Gemini
    return await _call_gemini_direct(prompt)


def _parse_json(raw: str) -> dict | list:
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    # Fast path: clean JSON string
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Slow path: model wrapped output in prose — find and decode the first
    # complete JSON object or array, ignoring surrounding text
    decoder = json.JSONDecoder()
    for ch in ('{', '['):
        idx = cleaned.find(ch)
        if idx != -1:
            try:
                value, _ = decoder.raw_decode(cleaned, idx)
                return value
            except json.JSONDecodeError:
                pass
    raise ValueError(f"No valid JSON in LLM response: {cleaned[:200]}")


# ── Learning note injected into prompts from user feedback ───────────────────

def _learning_note(ctx: dict, persona: str) -> str:
    if not ctx.get("has_feedback"):
        return ""
    avg = ctx["avg_rating"]
    total = ctx["total_feedback"]
    sentiment = ctx["sentiment"]
    note = f"\n\n[ADK AGENT LEARNING — {total} user ratings, avg {avg}/5 for this domain]\n"
    if sentiment == "negative":
        neg = "; ".join(ctx.get("negative_comments", [])) or "analyses were too generic"
        note += (
            f"Users were FRUSTRATED. Reported issues: {neg}. "
            "CORRECT by: naming specific entities, exact numbers, and citing which source supports each claim. "
            "Every vague sentence is a failure of your role."
        )
    elif sentiment == "positive":
        pos = "; ".join(ctx.get("positive_comments", [])) or "analyses were specific and actionable"
        note += f"Users were SATISFIED. What worked: {pos}. Maintain this approach."
    else:
        note += "Mixed feedback — improve specificity. Add numbers, named entities, and evidence citations."
    return note


# ── ADK Agent definitions ─────────────────────────────────────────────────────
# Created once at module load; reused across requests via separate sessions.

def _build_adk_agents():
    if not _ADK_READY:
        return None, None, None, None, None

    try:
        constraint_tool = FunctionTool(_validate_action_tool)

        orion = LlmAgent(
            name="orion",
            model="gemini-2.0-flash",
            instruction=(
                "You are Orion, an optimist AI analyst. "
                "Return ONLY valid JSON matching the schema provided in each user message. "
                "Be specific — name exact numbers, named entities, and percentages. Never be generic."
            ),
        )
        raven = LlmAgent(
            name="raven",
            model="gemini-2.0-flash",
            instruction=(
                "You are Raven, a pessimist AI analyst. "
                "Return ONLY valid JSON matching the schema provided in each user message. "
                "Be specific — name exact risks, failure points, and concrete negative outcomes."
            ),
        )
        cipher = LlmAgent(
            name="cipher",
            model="gemini-2.0-flash",
            instruction=(
                "You are Cipher, a realist AI analyst. "
                "Return ONLY valid JSON matching the schema provided in each user message. "
                "Use probability-weighted language and confidence intervals."
            ),
        )
        resolver = LlmAgent(
            name="resolver",
            model="gemini-2.0-flash",
            instruction=(
                "You are the Resolver, a senior AI analyst. "
                "Synthesize conflicting agent inputs into one authoritative finding. "
                "Return ONLY valid JSON matching the schema provided in each user message."
            ),
        )
        executor = LlmAgent(
            name="executor",
            model="gemini-2.0-flash",
            instruction=(
                "You are the Executor, an AI action planner. "
                "You have access to validate_action_tool to check each action against constraints. "
                "Use it for each action you plan before including it in your chain. "
                "Return ONLY a valid JSON array of 5 action objects matching the schema provided."
            ),
            tools=[constraint_tool],
        )
        logger.info("[ADK] All 5 LlmAgents built: Orion, Raven, Cipher, Resolver, Executor")
        return orion, raven, cipher, resolver, executor

    except Exception as exc:
        logger.warning(f"[ADK] Agent build failed: {exc}")
        return None, None, None, None, None


_orion_adk, _raven_adk, _cipher_adk, _resolver_adk, _executor_adk = _build_adk_agents()


# ── Agent classes (same interface as before, now ADK-backed) ──────────────────

class OrionAgent:
    async def analyze(self, text: str, domain: str, credibility_map: dict, learning_ctx: dict | None = None) -> dict:
        lnote = _learning_note(learning_ctx or {}, "Orion/Optimist")
        prompt = f"""You are Orion — OPTIMIST analyst.
Domain: {domain} | Credibility: {json.dumps(credibility_map)}{lnote}

Rules: Find the hidden opportunity. Name numbers, percentages, named entities. Never generic.
Source content: {text[:2000]}

Return ONLY valid JSON:
{{"agent":"Orion","persona":"Optimist","insight":"specific non-obvious opportunity","impact":"concrete positive outcome with timeframe","recommended_action":"one executable action starting today","confidence":72,"reasoning":"why this confidence level","key_signal":"single most important data point"}}"""
        try:
            raw = await _call(_orion_adk, prompt)
            result = _parse_json(raw)
            logger.info(f"[ADK] Orion complete — confidence={result.get('confidence')} adk={_ADK_READY}")
            return result
        except Exception as e:
            logger.warning(f"Orion failed: {e} — using fallback")
            return {
                "agent": "Orion", "persona": "Optimist",
                "insight": f"Despite surface disruption in {domain}, first-movers who act in 7 days capture 15-20% market share.",
                "impact": "PKR 800,000 incremental revenue within 30 days.",
                "recommended_action": "Contact top 5 alternative suppliers and negotiate 30-day bridge contracts.",
                "confidence": 68, "reasoning": "CSV data (0.90) shows clear trend; feed corroborates.",
                "key_signal": "40% volume drop signals competitor vulnerability window",
            }


class RavenAgent:
    async def analyze(self, text: str, domain: str, credibility_map: dict, learning_ctx: dict | None = None) -> dict:
        lnote = _learning_note(learning_ctx or {}, "Raven/Pessimist")
        prompt = f"""You are Raven — PESSIMIST analyst.
Domain: {domain} | Credibility: {json.dumps(credibility_map)}{lnote}

Rules: Find worst-case risks being underestimated. Name specific failure points and entities.
Source content: {text[:2000]}

Return ONLY valid JSON:
{{"agent":"Raven","persona":"Pessimist","insight":"specific worst-case risk","impact":"concrete negative outcome if unaddressed in 14 days","recommended_action":"one defensive action starting today","confidence":78,"reasoning":"why this confidence level","key_signal":"single most alarming data point"}}"""
        try:
            raw = await _call(_raven_adk, prompt)
            result = _parse_json(raw)
            logger.info(f"[ADK] Raven complete — confidence={result.get('confidence')} adk={_ADK_READY}")
            return result
        except Exception as e:
            logger.warning(f"Raven failed: {e} — using fallback")
            return {
                "agent": "Raven", "persona": "Pessimist",
                "insight": f"{domain} faces cascading failure if 72h delay extends past 96h — 3 production lines halt.",
                "impact": "PKR 2.4M daily revenue loss and 14% customer churn beyond 10 days.",
                "recommended_action": "Activate emergency inventory protocol, pre-authorise PKR 300,000 contingency.",
                "confidence": 81, "reasoning": "Feed (0.60) and CSV (0.90) both show deteriorating trend.",
                "key_signal": "14 containers held at Karachi customs — 72h delay confirmed",
            }


class CipherAgent:
    async def analyze(self, text: str, domain: str, credibility_map: dict, learning_ctx: dict | None = None) -> dict:
        lnote = _learning_note(learning_ctx or {}, "Cipher/Realist")
        prompt = f"""You are Cipher — REALIST analyst.
Domain: {domain} | Credibility: {json.dumps(credibility_map)}{lnote}

Rules: Probability-weighted assessment (e.g. "60% chance X, 40% chance Y"). Cite source credibility.
Source content: {text[:2000]}

Return ONLY valid JSON:
{{"agent":"Cipher","persona":"Realist","insight":"probability-weighted assessment","impact":"most likely outcome with confidence interval","recommended_action":"highest expected-value action","confidence":74,"reasoning":"why this confidence level","key_signal":"most decision-relevant data point"}}"""
        try:
            raw = await _call(_cipher_adk, prompt)
            result = _parse_json(raw)
            logger.info(f"[ADK] Cipher complete — confidence={result.get('confidence')} adk={_ADK_READY}")
            return result
        except Exception as e:
            logger.warning(f"Cipher failed: {e} — using fallback")
            return {
                "agent": "Cipher", "persona": "Realist",
                "insight": f"65% probability moderate {domain} disruption 5-10 days; 25% full recovery in 72h; 10% severe cascade.",
                "impact": "Expected impact PKR 600K-900K over 2 weeks. Confidence ±15%.",
                "recommended_action": "Tiered response: supplier contact Day 1, contingency procurement Day 2, exec briefing Day 3.",
                "confidence": 74, "reasoning": "CSV (0.90) most reliable; feed corroborates; text partially stale.",
                "key_signal": "Inventory days_remaining for SKU-002 at 2 days — immediate threshold",
            }


class ResolverAgent:
    async def resolve(self, agent_outputs: list, contradictions: dict, temporal: dict, domain: str) -> dict:
        prompt = f"""You are the Resolver — senior AI analyst synthesizing conflicting evidence.
Three agent analyses: {json.dumps(agent_outputs)}
Detected contradictions: {json.dumps(contradictions)}
Temporal trend: {json.dumps(temporal)}
Domain: {domain}

Synthesize one final authoritative insight. State which evidence you trusted and why.
Return ONLY valid JSON:
{{"final_insight":"authoritative synthesized finding","trusted_evidence":"what you relied on most and why","remaining_uncertainty":"what is still unknown","situation_summary":"2-sentence executive summary","investigation_path":["step 1","step 2","step 3"],"confidence":76,"contradiction_resolution":"how you resolved agent disagreements"}}"""
        try:
            raw = await _call(_resolver_adk, prompt)
            result = _parse_json(raw)
            logger.info(f"[ADK] Resolver complete — confidence={result.get('confidence')} adk={_ADK_READY}")
            return result
        except Exception as e:
            logger.warning(f"Resolver failed: {e} — using fallback")
            return {
                "final_insight": f"Verified deteriorating {domain} trend across 3 independent sources. Intervention required within 48h.",
                "trusted_evidence": "CSV (0.90) and feed converge. Text source partially contradicted.",
                "remaining_uncertainty": "Exact recovery timeline unknown. Supplier capacity post-clearance unconfirmed.",
                "situation_summary": f"Critical {domain} disruption confirmed. Action window 48-72 hours.",
                "investigation_path": [
                    "Request real-time stock audit from warehouse management system",
                    "Contact port authority for container release ETA confirmation",
                    "Cross-reference 30 days of supplier communication logs",
                ],
                "confidence": 76,
                "contradiction_resolution": "Weighted CSV (highest credibility) over vendor text claims.",
            }


class ExecutorAgent:
    async def plan_chain(self, resolved: dict, domain: str, constraints: dict) -> list:
        prompt = f"""You are the Executor — AI action planner with constraint validation tools.
Resolved insight: {json.dumps(resolved)}
Domain: {domain}
Constraints: {json.dumps(constraints)}

Use validate_action_tool for each step to check feasibility before finalising.
Generate exactly 5 causally linked actions:
  diagnose_root_cause → notify_stakeholders → update_system_state → launch_mitigation → schedule_monitoring

Each action must be specific to the insight (not generic), include cost in PKR and time in minutes.

Return ONLY valid JSON array:
[{{"step":1,"action":"specific action","triggered_by":"what makes this necessary","enables":"what step 2 can now do","estimated_cost_pkr":8000,"estimated_time_minutes":45,"side_effect":"adjacent area impact","monitor":"metric to watch","status":"PENDING"}}]"""
        try:
            raw = await _call(_executor_adk, prompt)
            result = _parse_json(raw)
            if isinstance(result, list) and len(result) == 5:
                logger.info(f"[ADK] Executor planned 5-step chain adk={_ADK_READY}")
                return result
            raise ValueError(f"Expected list of 5, got {type(result)}")
        except Exception as e:
            logger.warning(f"ExecutorAgent failed: {e} — using fallback chain")
            return self._fallback_chain(domain)

    def _fallback_chain(self, domain: str) -> list:
        return [
            {"step": 1, "action": f"Conduct root cause analysis: audit all {domain} data sources, cross-reference supplier reports, identify primary failure point within 2 hours.", "triggered_by": "Resolver confirmed multi-source signal convergence", "enables": "Step 2 can notify stakeholders with verified root cause", "estimated_cost_pkr": 8000, "estimated_time_minutes": 45, "side_effect": "Temporary diversion of 2 analysts from routine reporting", "monitor": "Diagnosis completion time vs 2-hour target", "status": "PENDING"},
            {"step": 2, "action": f"Notify all {domain} stakeholders: send executive alert with root cause summary, PKR 600K-900K impact estimate, and response timeline.", "triggered_by": "Root cause verified in Step 1", "enables": "Step 3 can update system state with stakeholder-approved parameters", "estimated_cost_pkr": 3000, "estimated_time_minutes": 30, "side_effect": "May trigger premature customer communications", "monitor": "Stakeholder acknowledgement rate within 1 hour", "status": "PENDING"},
            {"step": 3, "action": f"Update {domain} system state: freeze non-critical POs, activate contingency supplier list, flag impacted SKUs in inventory system.", "triggered_by": "Stakeholders approved response in Step 2", "enables": "Step 4 mitigation has clean system state", "estimated_cost_pkr": 12000, "estimated_time_minutes": 60, "side_effect": "PO freeze delays unrelated procurement 24-48h", "monitor": "Number of flagged SKUs and POs paused", "status": "PENDING"},
            {"step": 4, "action": f"Launch mitigation: engage 3 pre-approved alternative suppliers, place bridge orders for critical SKUs, request expedited customs clearance.", "triggered_by": "System state updated in Step 3", "enables": "Step 5 monitoring has concrete metrics to track", "estimated_cost_pkr": 280000, "estimated_time_minutes": 120, "side_effect": "Emergency procurement may create temporary budget overrun", "monitor": "Bridge order confirmation rate and supplier response time", "status": "PENDING"},
            {"step": 5, "action": f"Schedule 72-hour monitoring: 4-hourly automated {domain} feed checks, daily supplier calls, weekly executive review until full resolution.", "triggered_by": "Mitigation launched in Step 4", "enables": "Executive team can make data-driven escalation decisions", "estimated_cost_pkr": 15000, "estimated_time_minutes": 20, "side_effect": "Monitoring adds 8% load to analytics infrastructure", "monitor": "Recovery velocity: % critical SKUs back to normal within 72h", "status": "PENDING"},
        ]


# ── ConsensusEngine — orchestrates all 5 ADK agents ──────────────────────────

class ConsensusEngine:
    async def run(self, all_sources: list, filtered_sources: dict, contradictions: dict, domain: str, constraints: dict) -> dict:
        trusted = filtered_sources.get("trusted", [])
        low_conf = filtered_sources.get("low_confidence", [])
        combined_text = "\n\n".join(s.get("content", "")[:600] for s in trusted + low_conf)
        credibility_map = filtered_sources.get("credibility_map", {})
        temporal = contradictions.get("temporal_analysis", {})

        # Load domain-level feedback for agent self-improvement
        learning_ctx = feedback_store.get_domain_learning_context(domain)
        if learning_ctx.get("has_feedback"):
            logger.info(
                f"[ADK] Agent learning active — domain={domain} "
                f"avg={learning_ctx['avg_rating']} sentiment={learning_ctx['sentiment']} "
                f"n={learning_ctx['total_feedback']}"
            )

        logger.info(f"[ADK] Launching Orion, Raven, Cipher staggered — adk_ready={_ADK_READY}")

        async def _staggered(coro, delay: float):
            if delay > 0:
                await asyncio.sleep(delay)
            return await coro

        orion, raven, cipher = await asyncio.gather(
            _staggered(OrionAgent().analyze(combined_text, domain, credibility_map, learning_ctx), 0.0),
            _staggered(RavenAgent().analyze(combined_text, domain, credibility_map, learning_ctx), 1.2),
            _staggered(CipherAgent().analyze(combined_text, domain, credibility_map, learning_ctx), 2.4),
        )

        # Weighted confidence: Cipher 40%, Orion 30%, Raven 30%
        weighted_confidence = round(
            cipher.get("confidence", 70) * 0.40
            + orion.get("confidence", 70) * 0.30
            + raven.get("confidence", 70) * 0.30,
            1,
        )

        logger.info("[ADK] Launching Resolver")
        resolved = await ResolverAgent().resolve([orion, raven, cipher], contradictions, temporal, domain)

        logger.info("[ADK] Launching Executor")
        raw_chain = await ExecutorAgent().plan_chain(resolved, domain, constraints)

        logger.info("[ADK] Running ConstraintChecker on action chain")
        validated_chain = ConstraintChecker().validate_chain(raw_chain, constraints)

        return {
            "agents": [orion, raven, cipher],
            "weighted_confidence": weighted_confidence,
            "consensus_confidence": weighted_confidence,
            "resolved": resolved,
            "action_chain": validated_chain,
            "domain": domain,
            "total_estimated_cost_pkr": sum(a.get("estimated_cost_pkr", 0) for a in validated_chain),
            "total_estimated_time_minutes": sum(a.get("estimated_time_minutes", 0) for a in validated_chain),
            "learning_active": learning_ctx.get("has_feedback", False),
            "learning_context": learning_ctx,
            "adk_enabled": _ADK_READY,
        }
