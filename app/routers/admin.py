import json
import datetime
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import APP_DIR, ADMIN_SESSION_COOKIE_NAME
from app.database import get_db, get_all_settings
from app.security import require_admin, decode_session_token

router = APIRouter(prefix="/admin", tags=["Admin Overview"])
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

@router.get("/login", response_class=HTMLResponse)
def admin_login_view(request: Request):
    token = request.cookies.get(ADMIN_SESSION_COOKIE_NAME)
    payload = decode_session_token(token) if token else None
    if payload and "sub" in payload and payload.get("role") in ("admin", "superadmin"):
        return RedirectResponse("/admin", status_code=302)
    settings = get_all_settings()
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "store_settings": settings
    })

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def admin_overview(request: Request, admin: dict = Depends(require_admin)):
    settings = get_all_settings()

    with get_db() as conn:
        total_rev = conn.execute("SELECT COALESCE(SUM(total_amount), 0) as rev FROM orders WHERE payment_status = 'PAID'").fetchone()["rev"]
        paid_orders_count = conn.execute("SELECT COUNT(*) as cnt FROM orders WHERE payment_status = 'PAID'").fetchone()["cnt"]
        total_orders = conn.execute("SELECT COUNT(*) as cnt FROM orders").fetchone()["cnt"]
        pending_orders = conn.execute("SELECT COUNT(*) as cnt FROM orders WHERE payment_status = 'PENDING'").fetchone()["cnt"]
        total_customers = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE role = 'customer'").fetchone()["cnt"]
        active_products = conn.execute("SELECT COUNT(*) as cnt FROM products WHERE status = 'active'").fetchone()["cnt"]
        inactive_products = conn.execute("SELECT COUNT(*) as cnt FROM products WHERE status != 'active'").fetchone()["cnt"]

        recent_orders = conn.execute("""
            SELECT id, order_number, customer_name, customer_email, total_amount, payment_status, created_at
            FROM orders
            ORDER BY id DESC
            LIMIT 5
        """).fetchall()

        top_products = conn.execute("""
            SELECT oi.product_name, SUM(oi.quantity) as total_sold, SUM(oi.subtotal) as total_revenue
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.payment_status = 'PAID'
            GROUP BY oi.product_name
            ORDER BY total_sold DESC
            LIMIT 5
        """).fetchall()

        today = datetime.date.today()
        chart_points = []
        for i in range(6, -1, -1):
            day = today - datetime.timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            day_label = day.strftime("%d/%m")
            rev_day = conn.execute("""
                SELECT COALESCE(SUM(total_amount), 0) as rev
                FROM orders
                WHERE payment_status = 'PAID' AND DATE(created_at) = ?
            """, (day_str,)).fetchone()["rev"]
            chart_points.append({"label": day_label, "value": rev_day})

    stats = {
        "total_revenue": total_rev,
        "paid_orders_count": paid_orders_count,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_customers": total_customers,
        "active_products": active_products,
        "inactive_products": inactive_products
    }

    ctx = {
        "request": request,
        "current_admin": admin,
        "store_settings": settings,
        "active_nav": "overview",
        "stats": stats,
        "recent_orders": [dict(r) for r in recent_orders],
        "top_products": [dict(tp) for tp in top_products],
        "chart_data_json": json.dumps(chart_points)
    }
    return templates.TemplateResponse("admin/overview.html", ctx)

@router.get("/audit-logs", response_class=HTMLResponse)
def admin_audit_logs(request: Request, admin: dict = Depends(require_admin)):
    settings = get_all_settings()
    with get_db() as conn:
        logs = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100").fetchall()

    ctx = {
        "request": request,
        "current_admin": admin,
        "store_settings": settings,
        "active_nav": "audit",
        "logs": [dict(l) for l in logs]
    }
    return templates.TemplateResponse("admin/audit_logs.html", ctx)
