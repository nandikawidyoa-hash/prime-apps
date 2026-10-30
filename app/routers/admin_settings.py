import io
import csv
import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Request, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import APP_DIR
from app.database import get_db, get_all_settings, set_setting, log_audit
from app.models import StoreSettingsRequest
from app.security import require_admin, hash_password, verify_password

router = APIRouter(tags=["Admin Settings & Reports"])
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

class AdminCredentialsRequest(BaseModel):
    email: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None

@router.get("/admin/settings", response_class=HTMLResponse)
def store_settings_view(request: Request, admin: dict = Depends(require_admin)):
    settings = get_all_settings()
    ctx = {
        "request": request,
        "current_admin": admin,
        "store_settings": settings,
        "settings": settings,
        "active_nav": "settings"
    }
    return templates.TemplateResponse("admin/settings.html", ctx)

@router.post("/api/admin/settings")
def update_store_settings(payload: StoreSettingsRequest, request: Request, admin: dict = Depends(require_admin)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    fields = payload.dict(exclude_unset=True)

    for k, v in fields.items():
        if v is not None:
            set_setting(k, str(v).strip())

    log_audit(admin["id"], admin["email"], "SETTINGS_UPDATED", "store_settings", "global", f"Mengubah {len(fields)} pengaturan toko", client_ip)
    return {"status": "success", "message": "Pengaturan berhasil diperbarui"}

@router.post("/api/admin/change-credentials")
def change_admin_credentials(payload: AdminCredentialsRequest, request: Request, admin: dict = Depends(require_admin)):
    admin_id = admin["id"]
    new_email = payload.email.strip().lower() if payload.email else None
    new_pwd = payload.new_password.strip() if payload.new_password else None

    with get_db() as conn:
        current_user = conn.execute("SELECT id, email, password_hash FROM users WHERE id = ?", (admin_id,)).fetchone()
        if not current_user:
            raise HTTPException(status_code=404, detail="Akun admin tidak ditemukan")

        # If changing password, verify current password
        if new_pwd:
            if not payload.current_password or not verify_password(payload.current_password, current_user["password_hash"]):
                raise HTTPException(status_code=400, detail="Kata sandi saat ini tidak cocok")
            if len(new_pwd) < 6:
                raise HTTPException(status_code=400, detail="Kata sandi baru minimal harus 6 karakter")
            new_hash = hash_password(new_pwd)
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, admin_id))

        if new_email and new_email != current_user["email"]:
            exist = conn.execute("SELECT id FROM users WHERE email = ? AND id != ?", (new_email, admin_id)).fetchone()
            if exist:
                raise HTTPException(status_code=400, detail="Alamat email sudah dipakai akun lain")
            conn.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, admin_id))

    log_audit(admin_id, new_email or admin["email"], "ADMIN_CREDENTIALS_CHANGED", "users", str(admin_id), "Admin memperbarui email/password", request.client.host if request.client else None)
    return {"status": "success", "message": "Email dan kata sandi admin berhasil diperbarui!"}

@router.get("/admin/reports", response_class=HTMLResponse)
def sales_reports_view(
    request: Request,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    settings = get_all_settings()
    today = datetime.date.today()
    if not start_date:
        start_date = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")

    with get_db() as conn:
        tx_rows = conn.execute("""
            SELECT id, order_number, customer_name, customer_email, payment_method,
                   subtotal, discount_amount, total_amount, payment_status, created_at
            FROM orders
            WHERE payment_status = 'PAID' AND DATE(created_at) >= ? AND DATE(created_at) <= ?
            ORDER BY id DESC
        """, (start_date, end_date)).fetchall()

        total_rev = conn.execute("""
            SELECT COALESCE(SUM(total_amount), 0) as rev, COUNT(*) as cnt
            FROM orders
            WHERE payment_status = 'PAID' AND DATE(created_at) >= ? AND DATE(created_at) <= ?
        """, (start_date, end_date)).fetchone()

        all_orders_cnt = conn.execute("""
            SELECT COUNT(*) as cnt
            FROM orders
            WHERE DATE(created_at) >= ? AND DATE(created_at) <= ?
        """, (start_date, end_date)).fetchone()["cnt"]

    paid_orders = total_rev["cnt"]
    total_revenue = total_rev["rev"]
    avg_order = int(total_revenue / paid_orders) if paid_orders > 0 else 0
    success_rate = int((paid_orders / all_orders_cnt) * 100) if all_orders_cnt > 0 else 0

    summary = {
        "start_date": start_date,
        "end_date": end_date,
        "total_revenue": total_revenue,
        "paid_orders": paid_orders,
        "all_orders_count": all_orders_cnt,
        "avg_order_value": avg_order,
        "success_rate": success_rate,
        "transactions": [dict(t) for t in tx_rows]
    }

    ctx = {
        "request": request,
        "current_admin": admin,
        "store_settings": settings,
        "summary": summary,
        "active_nav": "reports"
    }
    return templates.TemplateResponse("admin/reports.html", ctx)

@router.get("/api/admin/reports/export.csv")
def export_sales_csv(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    admin: dict = Depends(require_admin)
):
    today = datetime.date.today()
    if not start_date:
        start_date = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = today.strftime("%Y-%m-%d")

    with get_db() as conn:
        rows = conn.execute("""
            SELECT order_number, customer_name, customer_email, customer_phone,
                   payment_method, subtotal, discount_amount, total_amount,
                   payment_status, fulfillment_status, created_at
            FROM orders
            WHERE DATE(created_at) >= ? AND DATE(created_at) <= ?
            ORDER BY id DESC
        """, (start_date, end_date)).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Nomor Pesanan", "Nama Pelanggan", "Email", "No WhatsApp",
        "Metode Pembayaran", "Subtotal (IDR)", "Diskon (IDR)", "Total Bayar (IDR)",
        "Status Pembayaran", "Pengiriman Lisensi", "Tanggal Transaksi"
    ])

    for r in rows:
        writer.writerow([
            r["order_number"], r["customer_name"], r["customer_email"], r["customer_phone"] or "",
            r["payment_method"], r["subtotal"], r["discount_amount"], r["total_amount"],
            r["payment_status"], r["fulfillment_status"], r["created_at"]
        ])

    csv_data = output.getvalue()
    filename = f"laporan_penjualan_{start_date}_sd_{end_date}.csv"
    
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
