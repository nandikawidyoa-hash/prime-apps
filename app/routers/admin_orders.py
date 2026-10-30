from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Request, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import APP_DIR
from app.database import get_db, get_all_settings, log_audit
from app.security import require_admin
from app.routers.payments import fulfill_order_digital_licenses

router = APIRouter(tags=["Admin Orders"])
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

class UpdateStatusRequest(BaseModel):
    status: str

class InternalNotesRequest(BaseModel):
    notes: str

class ItemLicenseOverride(BaseModel):
    license_code: str

@router.get("/admin/orders", response_class=HTMLResponse)
def list_orders_view(
    request: Request,
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    admin: dict = Depends(require_admin)
):
    settings = get_all_settings()
    with get_db() as conn:
        base_where = "WHERE 1=1"
        params = []
        if q:
            base_where += " AND (order_number LIKE ? OR customer_name LIKE ? OR customer_email LIKE ? OR customer_phone LIKE ?)"
            term = f"%{q.strip()}%"
            params.extend([term, term, term, term])
        if status:
            base_where += " AND payment_status = ?"
            params.append(status)
        if start_date:
            base_where += " AND DATE(created_at) >= ?"
            params.append(start_date)
        if end_date:
            base_where += " AND DATE(created_at) <= ?"
            params.append(end_date)

        # Count total orders matching filter
        count_query = f"SELECT COUNT(*) as cnt FROM orders {base_where}"
        total_count = conn.execute(count_query, params).fetchone()["cnt"]

        total_pages = max(1, (total_count + per_page - 1) // per_page)
        offset = (page - 1) * per_page

        query = f"SELECT * FROM orders {base_where} ORDER BY id DESC LIMIT ? OFFSET ?"
        rows = conn.execute(query, params + [per_page, offset]).fetchall()

    ctx = {
        "request": request,
        "current_admin": admin,
        "store_settings": settings,
        "active_nav": "orders",
        "orders": [dict(r) for r in rows],
        "query_q": q or "",
        "query_status": status or "",
        "start_date": start_date or "",
        "end_date": end_date or "",
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages
    }
    return templates.TemplateResponse("admin/orders.html", ctx)

@router.get("/admin/orders/{order_id}", response_class=HTMLResponse)
def order_detail_view(order_id: int, request: Request, admin: dict = Depends(require_admin)):
    settings = get_all_settings()
    with get_db() as conn:
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")

        items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()

    ctx = {
        "request": request,
        "current_admin": admin,
        "store_settings": settings,
        "active_nav": "orders",
        "order": dict(order),
        "items": [dict(i) for i in items]
    }
    return templates.TemplateResponse("admin/order_detail.html", ctx)

@router.post("/api/admin/orders/{order_id}/status")
def update_order_status(order_id: int, payload: UpdateStatusRequest, request: Request, admin: dict = Depends(require_admin)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    new_status = payload.status.upper()

    with get_db() as conn:
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")

        conn.execute("UPDATE orders SET payment_status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, order_id))

        if new_status == "PAID":
            fulfill_order_digital_licenses(conn, order_id)

        log_audit(admin["id"], admin["email"], "ORDER_STATUS_CHANGED", "orders", str(order_id), f"Ubah status #{order['order_number']} ke {new_status}", client_ip, conn=conn)

    return {"status": "success", "new_status": new_status}

@router.post("/api/admin/orders/{order_id}/items/{item_id}/license")
def override_item_license(order_id: int, item_id: int, payload: ItemLicenseOverride, request: Request, admin: dict = Depends(require_admin)):
    code = payload.license_code.strip()
    client_ip = request.client.host if request.client else "127.0.0.1"
    with get_db() as conn:
        item = conn.execute("SELECT id, product_name FROM order_items WHERE id = ? AND order_id = ?", (item_id, order_id)).fetchone()
        if not item:
            raise HTTPException(status_code=404, detail="Item pesanan tidak ditemukan")

        conn.execute("UPDATE order_items SET digital_payload = ? WHERE id = ?", (code, item_id))
        conn.execute("UPDATE orders SET fulfillment_status = 'FULFILLED', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (order_id,))
        log_audit(admin["id"], admin["email"], "ORDER_LICENSE_OVERRIDDEN", "orders", str(order_id), f"Ubah kode serial lisensi #{item_id}: {code}", client_ip, conn=conn)

    return {"status": "success", "license_code": code}

@router.post("/api/admin/orders/{order_id}/notes")
def update_order_internal_notes(order_id: int, payload: InternalNotesRequest, request: Request, admin: dict = Depends(require_admin)):
    with get_db() as conn:
        conn.execute("UPDATE orders SET internal_notes = ? WHERE id = ?", (payload.notes, order_id))
    return {"status": "success"}
