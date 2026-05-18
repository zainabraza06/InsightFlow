import json
import uuid
import time
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "history.json"
MAX_PER_USER = 50


def _load() -> dict:
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    return {}


def _save(data: dict):
    HISTORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def save_entry(user_email: str, entry: dict) -> str:
    data = _load()
    if user_email not in data:
        data[user_email] = []
    record = {
        "id": str(uuid.uuid4()),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        **entry,
    }
    data[user_email].insert(0, record)
    data[user_email] = data[user_email][:MAX_PER_USER]
    _save(data)
    return record["id"]


def get_entries(user_email: str) -> list:
    data = _load()
    entries = data.get(user_email, [])
    # Return summary without full nested results to keep response small
    return [
        {
            "id": e["id"],
            "timestamp": e["timestamp"],
            "domain": e.get("domain", ""),
            "topic": e.get("topic", ""),
            "sources_processed": e.get("sources_processed", 0),
            "contradictions_found": e.get("contradictions_found", 0),
            "actions_total": e.get("actions_total", 0),
            "total_cost_pkr": e.get("total_cost_pkr", 0),
            "status": e.get("status", "completed"),
        }
        for e in entries
    ]


def get_entry(user_email: str, entry_id: str) -> dict | None:
    data = _load()
    for e in data.get(user_email, []):
        if e["id"] == entry_id:
            return e
    return None


def delete_entry(user_email: str, entry_id: str) -> bool:
    data = _load()
    entries = data.get(user_email, [])
    new_entries = [e for e in entries if e["id"] != entry_id]
    if len(new_entries) == len(entries):
        return False
    data[user_email] = new_entries
    _save(data)
    return True


def get_all_entries() -> list:
    data = _load()
    all_records = []
    for email, entries in data.items():
        for e in entries:
            # Create a shallow copy and include the user email
            all_records.append({
                "user_email": email,
                "id": e["id"],
                "timestamp": e["timestamp"],
                "domain": e.get("domain", ""),
                "topic": e.get("topic", ""),
                "sources_processed": e.get("sources_processed", 0),
                "contradictions_found": e.get("contradictions_found", 0),
                "actions_total": e.get("actions_total", 0),
                "total_cost_pkr": e.get("total_cost_pkr", 0),
                "status": e.get("status", "completed"),
            })
    all_records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return all_records
