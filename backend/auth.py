import json
import hashlib
import secrets
import time
import os
from pathlib import Path
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET = os.getenv("JWT_SECRET", "nexus-dev-secret-change-in-prod")
USERS_FILE = Path(__file__).parent / "users.json"
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


def _load_users() -> dict:
    if USERS_FILE.exists():
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    return {}


def _save_users(users: dict):
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def _hash(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password + SECRET).encode()).hexdigest()


def register_user(name: str, email: str, password: str) -> dict:
    if not name.strip() or not email.strip() or len(password) < 6:
        raise HTTPException(status_code=422, detail="Name, email, and password (min 6 chars) required")
    users = _load_users()
    key = email.strip().lower()
    if key in users:
        raise HTTPException(status_code=400, detail="Email already registered")
    salt = secrets.token_hex(16)
    users[key] = {"name": name.strip(), "email": key, "salt": salt, "password": _hash(password, salt)}
    _save_users(users)
    return {"token": _make_token(key), "user": {"name": name.strip(), "email": key}}


def login_user(email: str, password: str) -> dict:
    users = _load_users()
    key = email.strip().lower()
    u = users.get(key)
    if not u or _hash(password, u["salt"]) != u["password"]:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"token": _make_token(key), "user": {"name": u["name"], "email": key}}


def get_current_user(creds: HTTPAuthorizationCredentials = Security(bearer)) -> str:
    if not creds:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        return _decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_user_info(email: str) -> dict:
    users = _load_users()
    u = users.get(email, {})
    return {"name": u.get("name", ""), "email": email}


def update_user(email: str, name: str | None = None, password: str | None = None) -> dict:
    users = _load_users()
    u = users.get(email)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if name:
        u["name"] = name.strip()
    if password and len(password) >= 6:
        salt = secrets.token_hex(16)
        u["salt"] = salt
        u["password"] = _hash(password, salt)
    users[email] = u
    _save_users(users)
    return {"name": u["name"], "email": email}
