from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import APP_DIR
from app.database import get_db, get_all_settings, log_audit
from app.models import VoucherCreateRequest
from app.security import require_admin

router = APIRouter(tags=["Admin Vouchers"])
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

@router.get("/admin/vouchers", response_class=HTMLResponse)
def list_vouchers_view(request: Request, admin: dict = Depends(require_admin)):
    settings = get_all_settings()
    with get_db() as conn:
        vouchers = conn.execute("SELECT * FROM vouchers ORDER BY id DESC").fetchall()

    ctx = {
        "request": request,
        "current_admin": admin,
        "store_settings": settings,
        "active_nav": "vouchers",
        "vouchers": [dict(v) for v in vouchers]
    }
    return templates.TemplateResponse("admin/vouchers.html", ctx)

@router.post("/api/admin/vouchers")
def create_voucher(payload: VoucherCreateRequest, request: Request, admin: dict = Depends(require_admin)):
    code = payload.code.strip().upper()
    client_ip = request.client.host if request.client else "127.0.0.1"

    with get_db() as conn:
        existing = conn.execute("SELECT id FROM vouchers WHERE code = ?", (code,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Kode voucher sudah ada")

        cursor = conn.execute("""
            INSERT INTO vouchers (code, discount_type, discount_value, min_order_amount, usage_limit, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code, payload.discount_type, payload.discount_value, payload.min_order_amount, payload.usage_limit, 1 if payload.is_active else 0))
        voucher_id = cursor.lastrowid

    log_audit(admin["id"], admin["email"], "VOUCHER_CREATED", "vouchers", str(voucher_id), f"Membuat voucher {code}", client_ip)
    return {"status": "success", "id": voucher_id, "code": code}

@router.delete("/api/admin/vouchers/{voucher_id}")
def delete_voucher(voucher_id: int, request: Request, admin: dict = Depends(require_admin)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    with get_db() as conn:
        conn.execute("DELETE FROM vouchers WHERE id = ?", (voucher_id,))
    log_audit(admin["id"], admin["email"], "VOUCHER_DELETED", "vouchers", str(voucher_id), "Menghapus voucher", client_ip)
    return {"status": "success"}
