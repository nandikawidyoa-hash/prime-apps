import hashlib
import hmac
import secrets
import time
import json
import base64
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from app.config import SECRET_KEY, SESSION_COOKIE_NAME, ADMIN_SESSION_COOKIE_NAME
from app.database import get_db

# PBKDF2-HMAC-SHA256 Implementation
ITERATIONS = 100000

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"pbkdf2:sha256:{ITERATIONS}${salt.hex()}${pwd_hash.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        meta, salt_hex, hash_hex = parts
        _, _, iters_str = meta.split(":")
        iterations = int(iters_str)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        actual_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False

# Token generator & signature (HMAC-SHA256)
def create_session_token(payload: Dict[str, Any], expiry_seconds: int = 86400 * 7) -> str:
    payload_copy = payload.copy()
    payload_copy["exp"] = int(time.time()) + expiry_seconds
    data_str = json.dumps(payload_copy, separators=(",", ":"))
    b64_data = base64.urlsafe_b64encode(data_str.encode("utf-8")).decode("utf-8").rstrip("=")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), b64_data.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{b64_data}.{signature}"

def decode_session_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        b64_data, signature = parts
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), b64_data.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        # Add padding back if necessary
        padding = "=" * ((4 - len(b64_data) % 4) % 4)
        data_str = base64.urlsafe_b64decode((b64_data + padding).encode("utf-8")).decode("utf-8")
        payload = json.loads(data_str)
        
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None

def get_current_user_optional(request: Request) -> Optional[dict]:
    # Check admin cookie first or customer session cookie
    token = request.cookies.get(ADMIN_SESSION_COOKIE_NAME) or request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        # Check Authorization header Bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
    
    if not token:
        return None

    payload = decode_session_token(token)
    if not payload or "sub" not in payload:
        return None

    user_id = payload["sub"]
    with get_db() as conn:
        row = conn.execute("SELECT id, email, full_name, phone, role, status FROM users WHERE id = ?", (user_id,)).fetchone()
        if row and row["status"] == "active":
            return dict(row)
    return None

def get_current_user_required(request: Request) -> dict:
    user = get_current_user_optional(request)
    if not user:
        if request.url.path.startswith("/api/"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autentikasi diperlukan")
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/login?next=" + request.url.path})
    return user

def require_admin(request: Request) -> dict:
    token = request.cookies.get(ADMIN_SESSION_COOKIE_NAME)
    payload = decode_session_token(token) if token else None
    
    user = None
    if payload and "sub" in payload:
        with get_db() as conn:
            row = conn.execute("SELECT id, email, full_name, phone, role, status FROM users WHERE id = ?", (payload["sub"],)).fetchone()
            if row and row["status"] == "active" and row["role"] in ("admin", "superadmin"):
                user = dict(row)

    if not user:
        # Also check normal session
        candidate = get_current_user_optional(request)
        if candidate and candidate["role"] in ("admin", "superadmin"):
            user = candidate

    if not user:
        if request.url.path.startswith("/api/"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses admin ditolak")
        raise HTTPException(status_code=status.HTTP_307_TEMPORARY_REDIRECT, headers={"Location": "/admin/login?next=" + request.url.path})
    return user

def require_superadmin(request: Request) -> dict:
    user = require_admin(request)
    if user["role"] != "superadmin":
        if request.url.path.startswith("/api/"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hanya Superadmin yang memiliki akses")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Halaman ini hanya untuk Superadmin")
    return user
