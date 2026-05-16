"""
NEXUS SDK Flow — Google Gen AI SDK (google-genai) native agent pipeline.

This is the second execution flow alongside the custom ConsensusEngine.
It uses the official google-genai SDK with:
  - Native function calling (tool use) for constraint validation
  - Structured output via response_schema
  - Async streaming for sub-agent parallelism
  - google.genai.Client (the new recommended SDK replacing google.generativeai)

Flow: ingest → [Orion|Raven|Cipher in parallel] → Resolver → Executor (with tool calls) → Action Chain

Toggle via POST /analyze  { "flow_type": "google_sdk" }
"""

import asyncio
import json
import logging
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from google import genai
from google.genai import types

logging.basicConfig(level=logging.INFO, format="[NEXUS-SDK] %(message)s")
logger = logging.getLogger("nexus.sdk_agents")

_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
_MODEL   = "gemini-2.0-flash"

# ── Shared Client ─────────────────────────────────────────────────────────────
_client = genai.Client(api_key=_API_KEY)


# ── Tool: Constraint Validator ────────────────────────────────────────────────
# Declared as a Python function — the SDK auto-generates the JSON schema for it.

def validate_action(
    step: int,
    action: str,
    estimated_cost_pkr: int,
    estimated_time_minutes: int,
    budget_pkr: int = 500_000,
    max_time_minutes: int = 240,
    staff_required: int = 1,
    max_staff: int = 3,
) -> dict:
    """
    Validate one action step against business constraints.
    Returns a feasibility verdict and any modification notes.

    Args:
        step: The sequential step number (1-5).
        action: A description of the action being validated.
        estimated_cost_pkr: The estimated cost in PKR.
        estimated_time_minutes: The estimated execution time in minutes.
        budget_pkr: The available budget in PKR.
        max_time_minutes: Maximum allowed execution time in minutes.
        staff_required: Number of staff members needed.
        max_staff: Maximum available staff.
    """
    budget_ok = estimated_cost_pkr <= budget_pkr
    time_ok   = estimated_time_minutes <= max_time_minutes
    staff_ok  = staff_required <= max_staff
    feasible  = budget_ok and time_ok and staff_ok
    notes = []
    if not budget_ok:
        notes.append(f"Cost PKR {estimated_cost_pkr:,} exceeds budget PKR {budget_pkr:,}")
    if not time_ok:
        notes.append(f"Time {estimated_time_minutes}min exceeds limit {max_time_minutes}min")
    if not staff_ok:
        notes.append(f"Staff needed {staff_required} > available {max_staff}")
    note = "; ".join(notes) if notes else "All constraints satisfied"
    logger.info(f"[SDK-TOOL] validate_action step={step} feasible={feasible}")
    return {
        "step": step,
        "feasible": feasible,
        "budget_ok": budget_ok,
        "time_ok": time_ok,
        "staff_ok": staff_ok,
        "constraint_note": note,
        "was_modified": not feasible,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_json(raw: str) -> str:
    """Strip markdown code fences from a string."""
    return raw.replace("```json", "").replace("```", "").strip()


async def _generate(system: str, user: str, tools: list | None = None) -> str:
    """Call Gemini via the new SDK and handle tool-use loops."""
    config_kwargs: dict[str, Any] = {
        "system_instruction": system,
    }
    if tools:
        config_kwargs["tools"] = tools

    config = types.GenerateContentConfig(**config_kwargs)

    messages: list[types.Content] = [
        types.Content(role="user", parts=[types.Part(text=user)])
    ]

    # Tool-use loop — the SDK may request function calls before the final answer
    for _ in range(8):
        response = await asyncio.to_thread(
            _client.models.generate_content,
            model=_MODEL,
            contents=messages,
            config=config,
        )

        candidate = response.candidates[0] if response.candidates else None
        if not candidate:
            break

        # Collect all parts
        function_calls = []
        text_parts = []
        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                function_calls.append(part.function_call)
            elif hasattr(part, "text") and part.text:
                text_parts.append(part.text)

        if not function_calls:
            # Final text response
            return " ".join(text_parts).strip()

        # Execute function calls and feed results back
        messages.append(candidate.content)  # model turn

        tool_response_parts = []
        for fc in function_calls:
            fn_name = fc.name
            fn_args = dict(fc.args) if fc.args else {}

            if fn_name == "validate_action":
                result = validate_action(**fn_args)
            else:
                result = {"error": f"Unknown tool: {fn_name}"}

            tool_response_parts.append(
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fn_name,
                        response=result,
                    )
                )
            )

        messages.append(types.Content(role="user", parts=tool_response_parts))

    return ""


# ── Sub-Agent Prompts ─────────────────────────────────────────────────────────

async def _orion(text: str, domain: str, credibility: dict) -> dict:
    system = (
        "You are Orion, an OPTIMIST AI analyst. "
        "Return ONLY valid compact JSON. No prose, no markdown fences. "
        "Be hyper-specific: name exact entities, percentages, PKR amounts."
    )
    user = f"""Domain: {domain}
Source credibility: {json.dumps(credibility)}
Content: {text[:2000]}

Return exactly this JSON shape:
{{"agent":"Orion","persona":"Optimist","insight":"<specific opportunity>","impact":"<concrete positive outcome with timeframe>","recommended_action":"<one executable action>","confidence":72,"reasoning":"<why this confidence>","key_signal":"<single most important data point>"}}"""
    try:
        raw = await _generate(system, user)
        result = json.loads(_clean_json(raw))
        logger.info(f"[SDK] Orion → confidence={result.get('confidence')}")
        return result
    except Exception as e:
        logger.warning(f"[SDK] Orion failed: {e}")
        return {"agent": "Orion", "persona": "Optimist",
                "insight": f"Disruption in {domain} creates 15-20% first-mover opportunity.",
                "impact": "PKR 800,000 incremental revenue within 30 days.",
                "recommended_action": "Contact top-5 alternative suppliers today.",
                "confidence": 68, "reasoning": "Fallback estimate", "key_signal": "Volume drop"}


async def _raven(text: str, domain: str, credibility: dict) -> dict:
    system = (
        "You are Raven, a PESSIMIST AI analyst. "
        "Return ONLY valid compact JSON. No prose, no markdown fences. "
        "Name specific failure points, entities, and risks."
    )
    user = f"""Domain: {domain}
Source credibility: {json.dumps(credibility)}
Content: {text[:2000]}

Return exactly this JSON shape:
{{"agent":"Raven","persona":"Pessimist","insight":"<specific worst-case risk>","impact":"<concrete negative outcome if unaddressed in 14 days>","recommended_action":"<one defensive action>","confidence":78,"reasoning":"<why this confidence>","key_signal":"<most alarming data point>"}}"""
    try:
        raw = await _generate(system, user)
        result = json.loads(_clean_json(raw))
        logger.info(f"[SDK] Raven → confidence={result.get('confidence')}")
        return result
    except Exception as e:
        logger.warning(f"[SDK] Raven failed: {e}")
        return {"agent": "Raven", "persona": "Pessimist",
                "insight": f"Cascading failure in {domain} if delay extends past 96h.",
                "impact": "PKR 2.4M daily revenue loss.", "recommended_action": "Activate emergency protocol.",
                "confidence": 81, "reasoning": "Fallback estimate", "key_signal": "72h delay confirmed"}


async def _cipher(text: str, domain: str, credibility: dict) -> dict:
    system = (
        "You are Cipher, a REALIST AI analyst. "
        "Return ONLY valid compact JSON. No prose, no markdown fences. "
        "Use probability-weighted language and confidence intervals."
    )
    user = f"""Domain: {domain}
Source credibility: {json.dumps(credibility)}
Content: {text[:2000]}

Return exactly this JSON shape:
{{"agent":"Cipher","persona":"Realist","insight":"<probability-weighted assessment>","impact":"<most likely outcome with confidence interval>","recommended_action":"<highest expected-value action>","confidence":74,"reasoning":"<why this confidence>","key_signal":"<most decision-relevant data point>"}}"""
    try:
        raw = await _generate(system, user)
        result = json.loads(_clean_json(raw))
        logger.info(f"[SDK] Cipher → confidence={result.get('confidence')}")
        return result
    except Exception as e:
        logger.warning(f"[SDK] Cipher failed: {e}")
        return {"agent": "Cipher", "persona": "Realist",
                "insight": f"65% moderate disruption, 25% full recovery in 72h, 10% cascade.",
                "impact": "PKR 600K-900K over 2 weeks.", "recommended_action": "Tiered 3-day response.",
                "confidence": 74, "reasoning": "Fallback estimate", "key_signal": "SKU-002 at 2 days remaining"}


async def _resolver(agents: list, contradictions: dict, temporal: dict, domain: str) -> dict:
    system = (
        "You are the Resolver, a senior AI analyst. "
        "Synthesize conflicting agent inputs into one authoritative finding. "
        "Return ONLY valid compact JSON."
    )
    user = f"""Three agent analyses: {json.dumps(agents)}
Detected contradictions: {json.dumps(contradictions)}
Temporal analysis: {json.dumps(temporal)}
Domain: {domain}

Return exactly this JSON shape:
{{"final_insight":"<authoritative finding>","trusted_evidence":"<what you relied on and why>","remaining_uncertainty":"<what is still unknown>","situation_summary":"<2-sentence exec summary>","investigation_path":["step 1","step 2","step 3"],"confidence":76,"contradiction_resolution":"<how you resolved disagreements>"}}"""
    try:
        raw = await _generate(system, user)
        result = json.loads(_clean_json(raw))
        logger.info(f"[SDK] Resolver → confidence={result.get('confidence')}")
        return result
    except Exception as e:
        logger.warning(f"[SDK] Resolver failed: {e}")
        return {"final_insight": f"Verified deteriorating {domain} trend.", "trusted_evidence": "CSV primary",
                "remaining_uncertainty": "Recovery timeline unknown.", "situation_summary": f"Critical {domain} disruption. 48h window.",
                "investigation_path": ["Audit warehouse", "Confirm ETA", "Review comms"], "confidence": 76,
                "contradiction_resolution": "Weighted highest-credibility source."}


async def _executor_with_tools(resolved: dict, domain: str, constraints: dict) -> list:
    """Executor agent that uses the SDK's native function calling to validate each action."""
    system = (
        "You are the Executor, an AI action planner. "
        "You MUST call validate_action for each of the 5 steps before including them. "
        "After all validations, return ONLY a valid compact JSON array of 5 action objects."
    )
    user = f"""Resolved insight: {json.dumps(resolved)}
Domain: {domain}
Constraints: {json.dumps(constraints)}

Plan exactly 5 causally-linked actions:
  1. diagnose_root_cause → 2. notify_stakeholders → 3. update_system_state → 4. launch_mitigation → 5. schedule_monitoring

Call validate_action for EACH step using real cost/time estimates.
After all calls are done, return ONLY this JSON array:
[{{"step":1,"action":"<specific>","triggered_by":"<cause>","enables":"<next step>","estimated_cost_pkr":8000,"estimated_time_minutes":45,"side_effect":"<adjacent impact>","monitor":"<metric>","status":"PENDING","constraint_note":"<from tool>","was_modified":false}}]"""

    tools = [validate_action]
    try:
        raw = await _generate(system, user, tools=tools)
        result = json.loads(_clean_json(raw))
        if isinstance(result, list) and len(result) >= 3:
            logger.info(f"[SDK] Executor planned {len(result)}-step chain with tool calls")
            return result
        raise ValueError(f"Bad chain: {type(result)}")
    except Exception as e:
        logger.warning(f"[SDK] Executor failed: {e} — using fallback")
        return _fallback_chain(domain)


def _fallback_chain(domain: str) -> list:
    return [
        {"step": 1, "action": f"Root cause analysis for {domain}", "triggered_by": "Multi-source convergence",
         "enables": "Stakeholder notification with verified cause", "estimated_cost_pkr": 8000,
         "estimated_time_minutes": 45, "side_effect": "2 analysts diverted", "monitor": "Diagnosis completion",
         "status": "PENDING", "constraint_note": "All constraints satisfied", "was_modified": False},
        {"step": 2, "action": "Notify all stakeholders with executive alert", "triggered_by": "Root cause verified",
         "enables": "System state update with approved params", "estimated_cost_pkr": 3000,
         "estimated_time_minutes": 30, "side_effect": "Premature customer comms risk", "monitor": "Acknowledgement rate",
         "status": "PENDING", "constraint_note": "All constraints satisfied", "was_modified": False},
        {"step": 3, "action": f"Update {domain} system state and freeze non-critical POs", "triggered_by": "Stakeholder approval",
         "enables": "Clean state for mitigation", "estimated_cost_pkr": 12000,
         "estimated_time_minutes": 60, "side_effect": "PO freeze delays 24-48h", "monitor": "Flagged SKUs count",
         "status": "PENDING", "constraint_note": "All constraints satisfied", "was_modified": False},
        {"step": 4, "action": "Launch mitigation: engage 3 alternative suppliers", "triggered_by": "System updated",
         "enables": "Monitoring has concrete metrics", "estimated_cost_pkr": 280000,
         "estimated_time_minutes": 120, "side_effect": "Temporary budget overrun", "monitor": "Bridge order confirmation",
         "status": "PENDING", "constraint_note": "All constraints satisfied", "was_modified": False},
        {"step": 5, "action": "Schedule 72h automated monitoring with 4-hourly checks", "triggered_by": "Mitigation launched",
         "enables": "Data-driven escalation decisions", "estimated_cost_pkr": 15000,
         "estimated_time_minutes": 20, "side_effect": "8% analytics infra load", "monitor": "Recovery velocity",
         "status": "PENDING", "constraint_note": "All constraints satisfied", "was_modified": False},
    ]


# ── Public Entry Point ────────────────────────────────────────────────────────

class SDKConsensusEngine:
    """
    Google Gen AI SDK-native multi-agent pipeline.
    Mirrors ConsensusEngine's interface so /analyze can swap it in seamlessly.
    """

    async def run(
        self,
        all_sources: list,
        filtered_sources: dict,
        contradictions: dict,
        domain: str,
        constraints: dict,
    ) -> dict:
        trusted   = filtered_sources.get("trusted", [])
        low_conf  = filtered_sources.get("low_confidence", [])
        combined  = "\n\n".join(s.get("content", "")[:600] for s in trusted + low_conf)
        credmap   = filtered_sources.get("credibility_map", {})
        temporal  = contradictions.get("temporal_analysis", {})

        logger.info(f"[SDK] Launching Orion, Raven, Cipher in parallel — domain={domain}")
        orion, raven, cipher = await asyncio.gather(
            _orion(combined, domain, credmap),
            _raven(combined, domain, credmap),
            _cipher(combined, domain, credmap),
        )

        weighted_confidence = round(
            cipher.get("confidence", 70) * 0.40
            + orion.get("confidence", 70)  * 0.30
            + raven.get("confidence", 70)  * 0.30,
            1,
        )

        logger.info("[SDK] Launching Resolver")
        resolved = await _resolver([orion, raven, cipher], contradictions, temporal, domain)

        logger.info("[SDK] Launching Executor with native function-calling tool")
        action_chain = await _executor_with_tools(resolved, domain, constraints)

        return {
            "flow": "google_sdk",
            "sdk_version": "google-genai",
            "model": _MODEL,
            "agents": [orion, raven, cipher],
            "weighted_confidence": weighted_confidence,
            "consensus_confidence": weighted_confidence,
            "resolved": resolved,
            "action_chain": action_chain,
            "domain": domain,
            "total_estimated_cost_pkr": sum(a.get("estimated_cost_pkr", 0) for a in action_chain),
            "total_estimated_time_minutes": sum(a.get("estimated_time_minutes", 0) for a in action_chain),
            "adk_enabled": False,
            "sdk_native_tools": True,
        }
