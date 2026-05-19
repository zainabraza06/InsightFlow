"""
Feedback store — dual mode: Firestore (FIRESTORE_ENABLED=true) or JSON flat file.
Firestore collection: `feedback`  — each doc keyed by entry UUID.
"""
import json
import uuid
import time
import os
from pathlib import Path

FEEDBACK_FILE  = Path(__file__).parent / "feedback.json"
LEARNING_WINDOW = 15
_FIRESTORE     = os.environ.get("FIRESTORE_ENABLED", "false").lower() == "true"
_GCP_PROJECT   = os.environ.get("GCP_PROJECT", "insightflow-496519")

# ── Firestore client (lazy) ────────────────────────────────────────────────────
_fs = None

def _firestore():
    global _fs
    if _fs is None:
        from google.cloud import firestore
        _fs = firestore.Client(project=_GCP_PROJECT)
    return _fs


# ── JSON flat-file helpers ─────────────────────────────────────────────────────
def _load() -> dict:
    if FEEDBACK_FILE.exists():
        return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))
    return {"entries": []}

def _save(data: dict):
    FEEDBACK_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ── Public API ─────────────────────────────────────────────────────────────────

def save_feedback(
    user_email: str,
    rating: int,
    domain: str,
    comment: str = "",
    analysis_id: str = "",
    agent_confidences: dict | None = None,
) -> str:
    eid = str(uuid.uuid4())
    entry = {
        "id": eid,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user_email": user_email,
        "analysis_id": analysis_id,
        "rating": max(1, min(5, int(rating))),
        "domain": domain,
        "comment": comment.strip(),
        "agent_confidences": agent_confidences or {},
    }
    if _FIRESTORE:
        _firestore().collection("feedback").document(eid).set(entry)
    else:
        data = _load()
        data["entries"].insert(0, entry)
        _save(data)
    return eid


def _domain_entries(domain: str) -> list:
    if _FIRESTORE:
        docs = (
            _firestore().collection("feedback")
            .where("domain", "==", domain)
            .order_by("timestamp", direction="DESCENDING")
            .limit(LEARNING_WINDOW)
            .stream()
        )
        return [d.to_dict() for d in docs]
    else:
        return [e for e in _load()["entries"] if e.get("domain") == domain][:LEARNING_WINDOW]


def get_domain_learning_context(domain: str) -> dict:
    entries = _domain_entries(domain)
    if not entries:
        return {"has_feedback": False}
    avg = sum(e["rating"] for e in entries) / len(entries)
    sentiment = "positive" if avg >= 4.0 else "negative" if avg <= 2.5 else "neutral"
    return {
        "has_feedback": True,
        "avg_rating": round(avg, 2),
        "total_feedback": len(entries),
        "sentiment": sentiment,
        "negative_comments": [e["comment"] for e in entries if e["rating"] <= 2 and e.get("comment")][:3],
        "positive_comments": [e["comment"] for e in entries if e["rating"] >= 4 and e.get("comment")][:3],
    }


def get_global_stats() -> dict:
    if _FIRESTORE:
        docs = _firestore().collection("feedback").order_by("timestamp", direction="DESCENDING").limit(500).stream()
        entries = [d.to_dict() for d in docs]
    else:
        entries = _load()["entries"]
    if not entries:
        return {"total": 0, "avg_rating": 0.0, "by_domain": {}, "recent": []}
    avg = sum(e["rating"] for e in entries) / len(entries)
    by_domain: dict = {}
    for e in entries:
        d = e.get("domain", "Unknown")
        by_domain.setdefault(d, {"count": 0, "total": 0})
        by_domain[d]["count"] += 1
        by_domain[d]["total"] += e["rating"]
    return {
        "total": len(entries),
        "avg_rating": round(avg, 2),
        "by_domain": {k: {"count": v["count"], "avg_rating": round(v["total"] / v["count"], 2)}
                      for k, v in by_domain.items()},
        "recent": entries[:5],
    }


def get_user_feedback(user_email: str) -> list:
    if _FIRESTORE:
        docs = _firestore().collection("feedback").where("user_email", "==", user_email).stream()
        return [d.to_dict() for d in docs]
    else:
        return [e for e in _load()["entries"] if e.get("user_email") == user_email]


def get_all_feedback_entries() -> list:
    if _FIRESTORE:
        docs = _firestore().collection("feedback").order_by("timestamp", direction="DESCENDING").limit(500).stream()
        return [d.to_dict() for d in docs]
    else:
        return _load().get("entries", [])


def reset_all_feedback():
    if _FIRESTORE:
        for doc in _firestore().collection("feedback").stream():
            doc.reference.delete()
    else:
        _save({"entries": []})
