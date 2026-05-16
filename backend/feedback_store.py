"""
Feedback store — persists user ratings per analysis and exposes domain-level
learning context that agents inject into their Gemini prompts.
"""
import json
import uuid
import time
from pathlib import Path

FEEDBACK_FILE = Path(__file__).parent / "feedback.json"
LEARNING_WINDOW = 15  # most recent N entries per domain used for agent tuning


def _load() -> dict:
    if FEEDBACK_FILE.exists():
        return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    return {"entries": []}


def _save(data: dict):
    FEEDBACK_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_feedback(
    user_email: str,
    rating: int,
    domain: str,
    comment: str = "",
    analysis_id: str = "",
    agent_confidences: dict | None = None,
) -> str:
    data = _load()
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user_email": user_email,
        "analysis_id": analysis_id,
        "rating": max(1, min(5, int(rating))),
        "domain": domain,
        "comment": comment.strip(),
        "agent_confidences": agent_confidences or {},
    }
    data["entries"].insert(0, entry)
    _save(data)
    return entry["id"]


def get_domain_learning_context(domain: str) -> dict:
    """
    Returns a structured learning snapshot agents inject into Gemini prompts.
    Covers the most recent LEARNING_WINDOW feedback entries for the domain.
    """
    data = _load()
    entries = [e for e in data["entries"] if e.get("domain") == domain][:LEARNING_WINDOW]

    if not entries:
        return {"has_feedback": False}

    avg = sum(e["rating"] for e in entries) / len(entries)
    sentiment = "positive" if avg >= 4.0 else "negative" if avg <= 2.5 else "neutral"

    neg_comments = [e["comment"] for e in entries if e["rating"] <= 2 and e.get("comment")][:3]
    pos_comments = [e["comment"] for e in entries if e["rating"] >= 4 and e.get("comment")][:3]

    return {
        "has_feedback": True,
        "avg_rating": round(avg, 2),
        "total_feedback": len(entries),
        "sentiment": sentiment,
        "negative_comments": neg_comments,
        "positive_comments": pos_comments,
    }


def get_global_stats() -> dict:
    data = _load()
    entries = data["entries"]
    if not entries:
        return {"total": 0, "avg_rating": 0.0, "by_domain": {}, "recent": []}

    avg = sum(e["rating"] for e in entries) / len(entries)
    by_domain: dict[str, dict] = {}
    for e in entries:
        d = e.get("domain", "Unknown")
        if d not in by_domain:
            by_domain[d] = {"count": 0, "total": 0}
        by_domain[d]["count"] += 1
        by_domain[d]["total"] += e["rating"]

    return {
        "total": len(entries),
        "avg_rating": round(avg, 2),
        "by_domain": {
            k: {"count": v["count"], "avg_rating": round(v["total"] / v["count"], 2)}
            for k, v in by_domain.items()
        },
        "recent": entries[:5],
    }


def get_user_feedback(user_email: str) -> list:
    data = _load()
    return [e for e in data["entries"] if e.get("user_email") == user_email]
