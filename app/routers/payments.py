import hashlib
import json
import secrets
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from app.database import get_db, log_audit
from app.config import PAYMENT_SECRET

router = APIRouter(tags=["Payments"])

class SimulatePaymentPayload(BaseModel):
    action: str = "pay"

def fulfill_order_digital_licenses(conn, order_id: int):
    items = conn.execute("SELECT id, product_id, product_name, quantity, digital_payload FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    
    for item in items:
        if item["digital_payload"]:
            continue

        assigned_keys = []
        product_id = item["product_id"]
        qty = item["quantity"]

        if product_id:
            pool_keys = conn.execute("""
                SELECT id, license_code FROM license_keys 
                WHERE product_id = ? AND is_used = 0 
                LIMIT ?
            """, (product_id, qty)).fetchall()

            for pk in pool_keys:
                conn.execute("""
                    UPDATE license_keys 
                    SET is_used = 1, order_id = ?, used_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (order_id, pk["id"]))
                assigned_keys.append(pk["license_code"])

        while len(assigned_keys) < qty:
            gen_key = f"PRIME-2026-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
            if product_id:
                conn.execute("""
                    INSERT INTO license_keys (product_id, license_code, is_used, order_id, used_at)
                    VALUES (?, ?, 1, ?, CURRENT_TIMESTAMP)
                """, (product_id, gen_key, order_id))
            assigned_keys.append(gen_key)

        final_payload = ", ".join(assigned_keys)
        conn.execute("UPDATE order_items SET digital_payload = ? WHERE id = ?", (final_payload, item["id"]))

    conn.execute("UPDATE orders SET fulfillment_status = 'FULFILLED', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (order_id,))

@router.post("/api/payments/simulate/{order_number}")
def simulate_payment(order_number: str, payload: SimulatePaymentPayload, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"

    with get_db() as conn:
        order = conn.execute("SELECT * FROM orders WHERE order_number = ?", (order_number,)).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")

        if order["payment_status"] == "PAID":
            return {"status": "success", "message": "Pesanan sudah dalam status lunas (PAID)", "order_number": order_number}

        order_id = order["id"]

        if payload.action == "pay":
            conn.execute("""
                UPDATE orders 
                SET payment_status = 'PAID', updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (order_id,))

            conn.execute("""
                UPDATE payments 
                SET status = 'SETTLEMENT', raw_response = 'Simulated Payment Success'
                WHERE order_id = ?
            """, (order_id,))

            fulfill_order_digital_licenses(conn, order_id)

            log_audit(order["user_id"], order["customer_email"], "PAYMENT_SETTLED", "orders", str(order_id), f"Simulasi pembayaran sukses #{order_number}", client_ip, conn=conn)

            return {
                "status": "success",
                "message": "Pembayaran lunas! Lisensi digital telah diterbitkan.",
                "order_number": order_number
            }
        elif payload.action == "fail":
            conn.execute("UPDATE orders SET payment_status = 'FAILED' WHERE id = ?", (order_id,))
            return {"status": "failed", "message": "Pembayaran disimulasikan gagal"}
        else:
            conn.execute("UPDATE orders SET payment_status = 'EXPIRED' WHERE id = ?", (order_id,))
            return {"status": "expired", "message": "Pembayaran kadaluarsa"}

@router.post("/api/payments/webhook")
async def payment_gateway_webhook(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    order_number = body.get("order_id")
    status_code = body.get("status_code", "200")
    gross_amount = str(body.get("gross_amount", ""))
    signature_key = body.get("signature_key", "")
    transaction_status = body.get("transaction_status", "settlement")

    if not order_number:
        raise HTTPException(status_code=400, detail="order_id missing")

    expected_hash = hashlib.sha512(f"{order_number}{status_code}{gross_amount}{PAYMENT_SECRET}".encode("utf-8")).hexdigest()
    if signature_key and signature_key != expected_hash:
        raise HTTPException(status_code=403, detail="Invalid signature")

    with get_db() as conn:
        order = conn.execute("SELECT * FROM orders WHERE order_number = ?", (order_number,)).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        order_id = order["id"]

        if transaction_status in ("capture", "settlement", "success"):
            if order["payment_status"] != "PAID":
                conn.execute("UPDATE orders SET payment_status = 'PAID', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (order_id,))
                conn.execute("UPDATE payments SET status = 'SETTLEMENT', raw_response = ? WHERE order_id = ?", (json.dumps(body), order_id))
                fulfill_order_digital_licenses(conn, order_id)
                log_audit(order["user_id"], order["customer_email"], "WEBHOOK_PAYMENT_SETTLED", "orders", str(order_id), f"Webhook gateway lunas #{order_number}", client_ip, conn=conn)
        elif transaction_status in ("deny", "cancel", "expire"):
            conn.execute("UPDATE orders SET payment_status = 'FAILED' WHERE id = ?", (order_id,))

    return {"status": "OK"}
