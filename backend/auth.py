"""
Auth — dual mode: Firestore (FIRESTORE_ENABLED=true) or JSON flat file.
Firestore collection: `users`  — each doc keyed by email.
"""
import json
import hashlib
import secrets
import time
import os
from pathlib import Path
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET      = os.getenv("JWT_SECRET", "nexus-dev-secret-change-in-prod")
USERS_FILE  = Path(__file__).parent / "users.json"
_FIRESTORE  = os.environ.get("FIRESTORE_ENABLED", "false").lower() == "true"
_GCP_PROJECT = os.environ.get("GCP_PROJECT", "insightflow-496519")
bearer = HTTPBearer(auto_error=False)

try:
    import jwt as _jwt
    def _make_token(email: str) -> str:
        return _jwt.encode({"sub": email, "exp": int(time.time()) + 604800}, SECRET, algorithm="HS256")
    def _decode_token(token: str) -> str:
        return _jwt.decode(token, SECRET, algorithms=["HS256"])["sub"]
except ImportError:
    import base64 as _b64
    def _make_token(email: str) -> str:
        payload = json.dumps({"sub": email, "exp": int(time.time()) + 604800})
        return _b64.urlsafe_b64encode(payload.encode()).decode()
    def _decode_token(token: str) -> str:
        data = json.loads(_b64.urlsafe_b64decode(token + "=="))
        if data["exp"] < time.time():
            raise ValueError("expired")
        return data["sub"]


# ── Firestore client (lazy) ────────────────────────────────────────────────────
_fs = None

def _firestore():
    global _fs
    if _fs is None:
        from google.cloud import firestore
        _fs = firestore.Client(project=_GCP_PROJECT)
    return _fs


# ── User record helpers ────────────────────────────────────────────────────────

def _get_user(email: str) -> dict | None:
    if _FIRESTORE:
        doc = _firestore().collection("users").document(email).get()
        return doc.to_dict() if doc.exists else None
    else:
        return _load_users().get(email)

def _put_user(email: str, record: dict):
    if _FIRESTORE:
        _firestore().collection("users").document(email).set(record)
    else:
        users = _load_users()
        users[email] = record
        _save_users(users)

def _load_users() -> dict:
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    return {}

def _save_users(users: dict):
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")

def _hash(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password + SECRET).encode()).hexdigest()


# ── Public API ─────────────────────────────────────────────────────────────────

def register_user(name: str, email: str, password: str) -> dict:
    if not name.strip() or not email.strip() or len(password) < 6:
        raise HTTPException(status_code=422, detail="Name, email, and password (min 6 chars) required")
    key = email.strip().lower()
    if _get_user(key):
        raise HTTPException(status_code=400, detail="Email already registered")
    salt = secrets.token_hex(16)
    _put_user(key, {"name": name.strip(), "email": key, "salt": salt,
                    "password": _hash(password, salt), "is_admin": False})
    return {"token": _make_token(key), "user": {"name": name.strip(), "email": key, "is_admin": False}}


def login_user(email: str, password: str) -> dict:
    key = email.strip().lower()
    u = _get_user(key)
    if not u or _hash(password, u["salt"]) != u["password"]:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": _make_token(key), "user": {"name": u["name"], "email": key, "is_admin": u.get("is_admin", False)}}


def get_current_user(creds: HTTPAuthorizationCredentials = Security(bearer)) -> str:
    if not creds:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return _decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_user_info(email: str) -> dict:
    u = _get_user(email) or {}
    return {"name": u.get("name", ""), "email": email, "is_admin": u.get("is_admin", False)}


def is_admin_user(email: str) -> bool:
    u = _get_user(email) or {}
    return u.get("is_admin", False)


def update_user(email: str, name: str | None = None, password: str | None = None) -> dict:
    u = _get_user(email)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if name:
        u["name"] = name.strip()
    if password and len(password) >= 6:
        salt = secrets.token_hex(16)
        u["salt"] = salt
        u["password"] = _hash(password, salt)
    _put_user(email, u)
    return {"name": u["name"], "email": email}


def toggle_user_admin_role(email: str) -> dict:
    key = email.strip().lower()
    u = _get_user(key)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    u["is_admin"] = not u.get("is_admin", False)
    _put_user(key, u)
    return {"email": key, "is_admin": u["is_admin"]}


def get_all_users_list() -> list:
    if _FIRESTORE:
        docs = _firestore().collection("users").stream()
        return [{"name": d.to_dict().get("name", ""), "email": d.id,
                 "is_admin": d.to_dict().get("is_admin", False)} for d in docs]
    else:
        users = _load_users()
        return [{"name": u.get("name", ""), "email": email, "is_admin": u.get("is_admin", False)}
                for email, u in users.items()]


def seed_admin():
    admin_email = "admin@insightflow.ai"
    if not _get_user(admin_email):
        salt = secrets.token_hex(16)
        _put_user(admin_email, {
            "name": "InsightFlow Admin",
            "email": admin_email,
            "salt": salt,
            "password": _hash("admin12345", salt),
            "is_admin": True,
        })
        print(f"[AUTH] Admin seeded: {admin_email}")
