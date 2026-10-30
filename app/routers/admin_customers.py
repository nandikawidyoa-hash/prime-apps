from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Request, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import APP_DIR
from app.database import get_db, get_all_settings, log_audit
from app.security import require_admin

router = APIRouter(tags=["Admin Customers"])
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

class CustomerStatusUpdate(BaseModel):
    status: str

@router.get("/admin/customers", response_class=HTMLResponse)
def list_customers_view(
    request: Request,
    q: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    admin: dict = Depends(require_admin)
):
    settings = get_all_settings()
    with get_db() as conn:
        where_clause = "WHERE 1=1"
        params = []
        if q:
            where_clause += " AND (u.full_name LIKE ? OR u.email LIKE ? OR u.phone LIKE ?)"
            term = f"%{q.strip()}%"
            params.extend([term, term, term])

        # Count total
        count_query = f"SELECT COUNT(*) as cnt FROM users u {where_clause}"
        total_count = conn.execute(count_query, params).fetchone()["cnt"]

        total_pages = max(1, (total_count + per_page - 1) // per_page)
        offset = (page - 1) * per_page

        query = f"""
            SELECT u.id, u.email, u.full_name, u.phone, u.role, u.status, u.created_at,
                   COUNT(o.id) as total_orders,
                   COALESCE(SUM(CASE WHEN o.payment_status = 'PAID' THEN o.total_amount ELSE 0 END), 0) as total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            {where_clause}
            GROUP BY u.id
            ORDER BY u.id DESC
            LIMIT ? OFFSET ?
        """
        users = conn.execute(query, params + [per_page, offset]).fetchall()

    ctx = {
        "request": request,
        "current_admin": admin,
        "store_settings": settings,
        "active_nav": "customers",
        "customers": [dict(u) for u in users],
        "query_q": q or "",
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages
    }
    return templates.TemplateResponse("admin/customers.html", ctx)

@router.post("/api/admin/customers/{customer_id}/status")
def update_customer_status(customer_id: int, payload: CustomerStatusUpdate, request: Request, admin: dict = Depends(require_admin)):
    new_status = payload.status.lower()
    client_ip = request.client.host if request.client else "127.0.0.1"

    with get_db() as conn:
        target = conn.execute("SELECT id, email, role FROM users WHERE id = ?", (customer_id,)).fetchone()
        if not target:
            raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan")

        # Disallow suspending superadmin
        if target["role"] == "superadmin":
            raise HTTPException(status_code=400, detail="Tidak dapat menonaktifkan akun Superadmin")

        conn.execute("UPDATE users SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, customer_id))
        log_audit(admin["id"], admin["email"], "CUSTOMER_STATUS_CHANGED", "users", str(customer_id), f"Ubah status pelanggan {target['email']} ke {new_status}", client_ip, conn=conn)

    return {"status": "success", "new_status": new_status}
