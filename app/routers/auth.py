import time
from fastapi import APIRouter, Request, HTTPException, Response, status
from fastapi.responses import RedirectResponse, JSONResponse
from app.database import get_db, log_audit
from app.models import UserRegisterRequest, UserLoginRequest
from app.security import hash_password, verify_password, create_session_token
from app.config import SESSION_COOKIE_NAME, ADMIN_SESSION_COOKIE_NAME

router = APIRouter(tags=["Authentication"])

@router.post("/api/auth/register")
def register_customer(payload: UserRegisterRequest, request: Request, response: Response):
    email = payload.email.strip().lower()
    full_name = payload.full_name.strip()
    phone = payload.phone.strip() if payload.phone else None
    
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Alamat email sudah terdaftar. Silakan masuk.")

        pwd_hash = hash_password(payload.password)
        cursor = conn.execute("""
            INSERT INTO users (email, password_hash, full_name, phone, role, status)
            VALUES (?, ?, ?, ?, 'customer', 'active')
        """, (email, pwd_hash, full_name, phone))
        user_id = cursor.lastrowid

    log_audit(user_id, email, "USER_REGISTER", "users", str(user_id), f"Pelanggan baru terdaftar: {full_name}", request.client.host if request.client else None)

    # Issue session
    token = create_session_token({"sub": user_id, "email": email, "role": "customer", "name": full_name})
    res = JSONResponse({"status": "success", "message": "Pendaftaran berhasil", "role": "customer"})
    res.set_cookie(SESSION_COOKIE_NAME, token, httponly=True, max_age=86400 * 7, samesite="lax")
    return res

@router.post("/api/auth/login")
def login_customer(payload: UserLoginRequest, request: Request, response: Response):
    email = payload.email.strip().lower()
    with get_db() as conn:
        user = conn.execute("SELECT id, email, password_hash, full_name, role, status FROM users WHERE email = ?", (email,)).fetchone()
        if not user or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Email atau kata sandi tidak cocok")
            
        if user["status"] != "active":
            raise HTTPException(status_code=403, detail="Akun dinonaktifkan. Hubungi admin.")

    log_audit(user["id"], email, "USER_LOGIN", "users", str(user["id"]), "Login pengguna berhasil", request.client.host if request.client else None)

    token = create_session_token({"sub": user["id"], "email": email, "role": user["role"], "name": user["full_name"]})
    res = JSONResponse({"status": "success", "message": "Login berhasil", "role": user["role"]})
    res.set_cookie(SESSION_COOKIE_NAME, token, httponly=True, max_age=86400 * 7, samesite="lax")
    
    # If user is admin, also set admin cookie
    if user["role"] in ("admin", "superadmin"):
        res.set_cookie(ADMIN_SESSION_COOKIE_NAME, token, httponly=True, max_age=86400 * 7, samesite="lax")
        
    return res

@router.post("/api/auth/admin-login")
def login_admin(payload: UserLoginRequest, request: Request, response: Response):
    email = payload.email.strip().lower()
    with get_db() as conn:
        user = conn.execute("SELECT id, email, password_hash, full_name, role, status FROM users WHERE email = ?", (email,)).fetchone()
        if not user or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Email atau password admin salah")
            
        if user["status"] != "active":
            raise HTTPException(status_code=403, detail="Akun administrator dinonaktifkan")
            
        if user["role"] not in ("admin", "superadmin"):
            raise HTTPException(status_code=403, detail="Akun tidak memiliki otoritas Administrator")

    log_audit(user["id"], email, "ADMIN_LOGIN", "users", str(user["id"]), f"Login {user['role']} berhasil", request.client.host if request.client else None)

    token = create_session_token({"sub": user["id"], "email": email, "role": user["role"], "name": user["full_name"]})
    res = JSONResponse({"status": "success", "message": "Login admin berhasil", "role": user["role"]})
    res.set_cookie(ADMIN_SESSION_COOKIE_NAME, token, httponly=True, max_age=86400 * 7, samesite="lax")
    res.set_cookie(SESSION_COOKIE_NAME, token, httponly=True, max_age=86400 * 7, samesite="lax")
    return res

@router.get("/auth/logout")
def logout_customer():
    res = RedirectResponse("/", status_code=status.HTTP_302_FOUND)
    res.delete_cookie(SESSION_COOKIE_NAME)
    return res

@router.get("/admin/logout")
def logout_admin():
    res = RedirectResponse("/admin/login", status_code=status.HTTP_302_FOUND)
    res.delete_cookie(ADMIN_SESSION_COOKIE_NAME)
    return res
