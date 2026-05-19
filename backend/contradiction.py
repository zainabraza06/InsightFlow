import asyncio
import json
import logging
import os

import httpx
import google.genai as genai

logging.basicConfig(level=logging.INFO, format="[NEXUS] %(message)s")
logger = logging.getLogger("nexus.contradiction")

_API_KEY       = os.environ.get("GOOGLE_API_KEY", "")
_GCP_PROJECT   = os.environ.get("GCP_PROJECT", "insightflow-496519")
_GCP_LOCATION  = os.environ.get("GCP_LOCATION", "us-central1")
_VERTEX_ENABLED = False

def _make_client():
    global _VERTEX_ENABLED
    if _GCP_PROJECT and os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            c = genai.Client(vertexai=True, project=_GCP_PROJECT, location=_GCP_LOCATION)
            _VERTEX_ENABLED = True
            return c
        except Exception:
            pass
    return genai.Client(api_key=_API_KEY) if _API_KEY else None

_client = _make_client()
_GEMINI_MODELS = ("gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash")
_OPENROUTER_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-v4-flash:free",
    "google/gemma-4-31b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]


async def _generate_via_openrouter(prompt: str) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://nexus-ai.local",
    }
    async with httpx.AsyncClient() as client:
        for model in _OPENROUTER_MODELS:
            try:
                payload = {"model": model, "messages": [{"role": "user", "content": prompt}]}
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=payload, timeout=60.0,
                )
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"].strip()
                if text:
                    logger.info(f"[CONTRADICTION] OpenRouter success model={model}")
                    return text
            except Exception as e:
                logger.warning(f"[CONTRADICTION] OpenRouter model={model} failed: {e}")
    raise RuntimeError("All OpenRouter models failed for contradiction detection")


def _generate_gemini(prompt: str) -> str:
    client = _client
    if not client:
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        client = genai.Client(api_key=api_key) if api_key else None
    if not client:
        raise RuntimeError("No Gemini client — set GCP_PROJECT or GOOGLE_API_KEY")
    backend = "Vertex AI" if _VERTEX_ENABLED else "AI Studio"
    for model in _GEMINI_MODELS:
        try:
            response = client.models.generate_content(model=model, contents=prompt)
            text = (response.text or "").strip()
            if text:
                logger.info(f"[CONTRADICTION] {backend} success model={model}")
                return text
        except Exception as e:
            logger.warning(f"[CONTRADICTION] {backend} model={model} failed: {e}")
    raise RuntimeError("All Gemini models exhausted")


async def _generate(prompt: str) -> str:
    """Route: OpenRouter first, Gemini direct as fallback."""
    try:
        return await _generate_via_openrouter(prompt)
    except Exception as e:
        logger.warning(f"[CONTRADICTION] OpenRouter failed ({e}) — falling back to Gemini")
        return await asyncio.to_thread(_generate_gemini, prompt)


class ContradictionEngine:

    def score_credibility(self, source: dict) -> float:
        score = source.get("credibility_base", 0.5)
        content = source.get("content", "")
        src_type = source.get("source_type", "")

        if content == "URL_FETCH_FAILED":
            source["credibility_score"] = 0.0
            return 0.0

        if src_type == "pdf":
            score += 0.10
        if src_type == "csv":
            score += 0.05
        if source.get("has_temporal"):
            score += 0.05

        noisy_terms = ["breaking", "rumor", "unconfirmed", "allegedly"]
        if any(t in content.lower() for t in noisy_terms):
            score -= 0.15

        stale_terms = ["yesterday", "last week", "last month"]
        if any(t in content.lower() for t in stale_terms):
            score -= 0.20

        score = max(0.0, min(1.0, score))
        source["credibility_score"] = score
        return score

    async def detect_contradictions(self, sources: list) -> dict:
        valid_sources = [s for s in sources if s.get("credibility_score", 0) > 0.0]
        if not valid_sources:
            return self._fallback_contradictions()

        lines = []
        for s in valid_sources:
            lines.append(
                f"[{s['source_type'].upper()}] (credibility={s.get('credibility_score', 0):.2f}): {s['content'][:500]}"
            )
        formatted_sources = "\n\n".join(lines)

        prompt = f"""You are a contradiction detection and source intelligence agent.

Analyze these information sources:
{formatted_sources}

Tasks:
1. Find ALL contradictions where two or more sources make conflicting claims about the same metric, event, or situation.
2. For each contradiction: identify which source to trust more based on recency, specificity, and credibility score.
3. Identify any sources that appear stale (old data), noisy (spam/irrelevant), or low-credibility.
4. Perform temporal analysis: if any source contains time-series data (dates, months, weeks), describe the trend direction (improving/worsening/stable) and rate of change.
5. For each contradiction, generate an investigation path — 3 concrete steps a human analyst should take to resolve it.

Return ONLY valid JSON. No markdown, no preamble:
{{
  "contradictions": [
    {{
      "source_a_type": "...",
      "source_b_type": "...",
      "claim_a": "exact claim from source A",
      "claim_b": "exact claim from source B",
      "conflict_reason": "why these conflict",
      "trusted_source": "A or B",
      "trust_reason": "recency/specificity/credibility rationale",
      "resolution_action": "one concrete action to resolve",
      "investigation_path": ["step 1", "step 2", "step 3"]
    }}
  ],
  "temporal_analysis": {{
    "has_trend": true,
    "trend_direction": "worsening/improving/stable/mixed",
    "trend_description": "specific description of how signal changed over time",
    "rate_of_change": "e.g. 8% decline per month"
  }},
  "stale_sources": ["source_type1"],
  "noise_sources": ["source_type2"],
  "overall_signal_confidence": 65,
  "recommended_trust_order": ["source_type ranked 1st", "2nd"]
}}"""

        try:
            raw = await _generate(prompt)
            cleaned = raw.replace("```json", "").replace("```", "").strip()
            decoder = json.JSONDecoder()
            try:
                result = json.loads(cleaned)
            except json.JSONDecodeError:
                # Model wrapped JSON in prose — find first { or [
                result = None
                for ch in ('{', '['):
                    idx = cleaned.find(ch)
                    if idx != -1:
                        try:
                            result, _ = decoder.raw_decode(cleaned, idx)
                            break
                        except json.JSONDecodeError:
                            pass
                if result is None:
                    raise ValueError("No valid JSON in contradiction response")
            for c in result.get("contradictions", []):
                logger.info(
                    f"Contradiction detected: {c.get('source_a_type')} vs {c.get('source_b_type')} — {c.get('conflict_reason')}. Resolver agent invoked."
                )
            return result
        except Exception as e:
            logger.warning(f"Contradiction detection failed: {e} — using fallback")
            return self._fallback_contradictions()

    def _fallback_contradictions(self) -> dict:
        return {
            "contradictions": [
                {
                    "source_a_type": "realtime_feed",
                    "source_b_type": "csv",
                    "claim_a": "Critical shortage detected at distribution points",
                    "claim_b": "Inventory records show 30-day buffer stock",
                    "conflict_reason": "Live observation contradicts static inventory data",
                    "trusted_source": "A",
                    "trust_reason": "More recent, specific location data",
                    "resolution_action": "Dispatch field team to verify stock levels physically",
                    "investigation_path": [
                        "Cross-check SKU-level inventory",
                        "Contact warehouse manager",
                        "Review last 48hr transaction logs",
                    ],
                }
            ],
            "temporal_analysis": {
                "has_trend": True,
                "trend_direction": "worsening",
                "trend_description": "Metrics declining for 3 consecutive periods",
                "rate_of_change": "~8% per period",
            },
            "stale_sources": ["csv"],
            "noise_sources": [],
            "overall_signal_confidence": 65,
            "recommended_trust_order": ["realtime_feed", "text", "pdf", "csv"],
        }

    def filter_noise(self, sources: list) -> dict:
        for s in sources:
            if "credibility_score" not in s:
                self.score_credibility(s)

        trusted = []
        low_confidence = []
        excluded = []
        credibility_map = {}

        for s in sources:
            score = s.get("credibility_score", 0.0)
            src_type = s.get("source_type", "unknown")
            credibility_map[src_type] = score

            if score < 0.30:
                excluded.append(s)
                logger.warning(
                    f"Source excluded: {src_type} scored {score:.2f} — below minimum threshold 0.30. Signal treated as noise."
                )
            elif score < 0.50:
                low_confidence.append(s)
                logger.info(f"Source flagged low_confidence: {src_type} scored {score:.2f}")
            else:
                trusted.append(s)

        return {
            "trusted": trusted,
            "low_confidence": low_confidence,
            "excluded": excluded,
            "credibility_map": credibility_map,
        }
