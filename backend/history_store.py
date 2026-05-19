"""
History store — dual mode: Firestore (FIRESTORE_ENABLED=true) or JSON flat file.
Firestore collection: `history`  — each doc keyed by entry UUID.
"""
import json
import uuid
import time
import os
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "history.json"
MAX_PER_USER = 50
_FIRESTORE   = os.environ.get("FIRESTORE_ENABLED", "false").lower() == "true"
_GCP_PROJECT = os.environ.get("GCP_PROJECT", "insightflow-496519")

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
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return {}

def _save(data: dict):
    HISTORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ── Public API — same surface regardless of backend ───────────────────────────

def save_entry(user_email: str, entry: dict) -> str:
    eid = str(uuid.uuid4())
    record = {
        "id": eid,
        "user_email": user_email,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **entry,
    }
    if _FIRESTORE:
        _firestore().collection("history").document(eid).set(record)
        # Enforce MAX_PER_USER — delete oldest if over limit
        old = (
            _firestore().collection("history")
            .where("user_email", "==", user_email)
            .order_by("timestamp", direction="DESCENDING")
            .offset(MAX_PER_USER)
            .stream()
        )
        for doc in old:
            doc.reference.delete()
    else:
        data = _load()
        data.setdefault(user_email, []).insert(0, record)
        data[user_email] = data[user_email][:MAX_PER_USER]
        _save(data)
    return eid


def get_entries(user_email: str) -> list:
    def _summary(e):
        return {
            "id": e["id"],
            "timestamp": e.get("timestamp", ""),
            "domain": e.get("domain", ""),
            "topic": e.get("topic", ""),
            "sources_processed": e.get("sources_processed", 0),
            "contradictions_found": e.get("contradictions_found", 0),
            "actions_total": e.get("actions_total", 0),
            "total_cost_pkr": e.get("total_cost_pkr", 0),
            "status": e.get("status", "completed"),
        }

    if _FIRESTORE:
        docs = (
            _firestore().collection("history")
            .where("user_email", "==", user_email)
            .order_by("timestamp", direction="DESCENDING")
            .limit(MAX_PER_USER)
            .stream()
        )
        return [_summary(d.to_dict()) for d in docs]
    else:
        return [_summary(e) for e in _load().get(user_email, [])]


def get_entry(user_email: str, entry_id: str) -> dict | None:
    if _FIRESTORE:
        doc = _firestore().collection("history").document(entry_id).get()
        if doc.exists:
            e = doc.to_dict()
            if e.get("user_email") == user_email:
                return e
        return None
    else:
        for e in _load().get(user_email, []):
            if e["id"] == entry_id:
                return e
        return None


def delete_entry(user_email: str, entry_id: str) -> bool:
    if _FIRESTORE:
        doc = _firestore().collection("history").document(entry_id).get()
        if doc.exists and doc.to_dict().get("user_email") == user_email:
            doc.reference.delete()
            return True
        return False
    else:
        data = _load()
        entries = data.get(user_email, [])
        new = [e for e in entries if e["id"] != entry_id]
        if len(new) == len(entries):
            return False
        data[user_email] = new
        _save(data)
        return True


def get_all_entries() -> list:
    if _FIRESTORE:
        docs = (
            _firestore().collection("history")
            .order_by("timestamp", direction="DESCENDING")
            .limit(500)
            .stream()
        )
        return [d.to_dict() for d in docs]
    else:
        data = _load()
        all_records = []
        for email, entries in data.items():
            for e in entries:
                all_records.append({"user_email": email, **e})
        all_records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_records


def admin_delete_entry(entry_id: str) -> bool:
    if _FIRESTORE:
        ref = _firestore().collection("history").document(entry_id)
        if ref.get().exists:
            ref.delete()
            return True
        return False
    else:
        data = _load()
        for email in list(data.keys()):
            entries = data[email]
            new = [e for e in entries if e["id"] != entry_id]
            if len(new) < len(entries):
                data[email] = new
                _save(data)
                return True
        return False
