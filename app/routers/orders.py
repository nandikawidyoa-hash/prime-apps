import uuid
import datetime
import secrets
from typing import Optional
from fastapi import APIRouter, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from app.database import get_db, log_audit
from app.models import CartItemAddRequest, CheckoutRequest, ApplyVoucherRequest
from app.security import get_current_user_optional

router = APIRouter(tags=["Orders & Cart"])

def get_or_create_cart_id(request: Request, response: Response, conn) -> int:
    user = get_current_user_optional(request)
    if user:
        row = conn.execute("SELECT id FROM carts WHERE user_id = ?", (user["id"],)).fetchone()
        if row:
            return row["id"]
        cursor = conn.execute("INSERT INTO carts (user_id) VALUES (?)", (user["id"],))
        return cursor.lastrowid
    
    session_id = request.cookies.get("cart_session_id")
    if session_id:
        row = conn.execute("SELECT id FROM carts WHERE session_id = ?", (session_id,)).fetchone()
        if row:
            return row["id"]
            
    new_session_id = secrets.token_hex(16)
    cursor = conn.execute("INSERT INTO carts (session_id) VALUES (?)", (new_session_id,))
    response.set_cookie("cart_session_id", new_session_id, max_age=86400 * 30, httponly=True, samesite="lax")
    return cursor.lastrowid

@router.get("/api/cart/count")
def get_cart_count(request: Request):
    user = get_current_user_optional(request)
    session_id = request.cookies.get("cart_session_id")

    if not user and not session_id:
        return {"count": 0}

    with get_db() as conn:
        cart_row = None
        if user:
            cart_row = conn.execute("SELECT id FROM carts WHERE user_id = ?", (user["id"],)).fetchone()
        elif session_id:
            cart_row = conn.execute("SELECT id FROM carts WHERE session_id = ?", (session_id,)).fetchone()

        if not cart_row:
            return {"count": 0}

        cnt = conn.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM cart_items WHERE cart_id = ?", (cart_row["id"],)).fetchone()
        return {"count": cnt["total"]}

@router.post("/api/cart/items")
def add_to_cart(payload: CartItemAddRequest, request: Request, response: Response):
    with get_db() as conn:
        prod = conn.execute("SELECT id, name, status FROM products WHERE id = ?", (payload.product_id,)).fetchone()
        if not prod or prod["status"] != "active":
            raise HTTPException(status_code=404, detail="Produk tidak tersedia")

        cart_id = get_or_create_cart_id(request, response, conn)

        variant_name = payload.variant_name
        if payload.variant_id:
            v_row = conn.execute("SELECT id, name FROM product_variants WHERE id = ? AND product_id = ?", (payload.variant_id, payload.product_id)).fetchone()
            if v_row:
                variant_name = v_row["name"]

        if payload.variant_id:
            existing = conn.execute("SELECT id, quantity FROM cart_items WHERE cart_id = ? AND product_id = ? AND variant_id = ?", (cart_id, payload.product_id, payload.variant_id)).fetchone()
        else:
            existing = conn.execute("SELECT id, quantity FROM cart_items WHERE cart_id = ? AND product_id = ? AND (variant_id IS NULL OR variant_id = 0)", (cart_id, payload.product_id)).fetchone()

        if existing:
            new_qty = existing["quantity"] + payload.quantity
            conn.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_qty, existing["id"]))
        else:
            conn.execute("""
                INSERT INTO cart_items (cart_id, product_id, variant_id, variant_name, quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (cart_id, payload.product_id, payload.variant_id, variant_name, payload.quantity))

        cnt = conn.execute("SELECT SUM(quantity) as total FROM cart_items WHERE cart_id = ?", (cart_id,)).fetchone()
        return {"status": "success", "total_items": cnt["total"]}

@router.delete("/api/cart/items/{product_id}")
def remove_from_cart(product_id: int, request: Request, response: Response):
    with get_db() as conn:
        cart_id = get_or_create_cart_id(request, response, conn)
        conn.execute("DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?", (cart_id, product_id))
        cnt = conn.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM cart_items WHERE cart_id = ?", (cart_id,)).fetchone()
        return {"status": "success", "total_items": cnt["total"]}

@router.post("/api/vouchers/apply")
def apply_voucher(payload: ApplyVoucherRequest):
    code = payload.code.strip().upper()
    with get_db() as conn:
        v = conn.execute("SELECT * FROM vouchers WHERE code = ? AND is_active = 1", (code,)).fetchone()
        if not v:
            raise HTTPException(status_code=400, detail="Kode voucher tidak valid atau telah berakhir")

        if v["usage_limit"] > 0 and v["times_used"] >= v["usage_limit"]:
            raise HTTPException(status_code=400, detail="Kuota voucher telah habis")

        if v["min_order_amount"] > 0 and payload.subtotal < v["min_order_amount"]:
            raise HTTPException(status_code=400, detail=f"Minimal pembelian untuk voucher ini adalah Rp {v['min_order_amount']:,}")

        discount = 0
        if v["discount_type"] == "percentage":
            discount = int((payload.subtotal * v["discount_value"]) / 100)
            if v["max_discount"] > 0 and discount > v["max_discount"]:
                discount = v["max_discount"]
        else:
            discount = min(v["discount_value"], payload.subtotal)

        return {
            "status": "success",
            "code": v["code"],
            "discount_amount": discount,
            "final_total": payload.subtotal - discount
        }

@router.post("/api/orders/checkout")
def create_order(payload: CheckoutRequest, request: Request, response: Response):
    user = get_current_user_optional(request)
    session_id = request.cookies.get("cart_session_id")
    client_ip = request.client.host if request.client else "127.0.0.1"

    with get_db() as conn:
        cart_row = None
        if user:
            cart_row = conn.execute("SELECT id FROM carts WHERE user_id = ?", (user["id"],)).fetchone()
        elif session_id:
            cart_row = conn.execute("SELECT id FROM carts WHERE session_id = ?", (session_id,)).fetchone()

        if not cart_row:
            raise HTTPException(status_code=400, detail="Keranjang belanja Anda kosong")

        cart_id = cart_row["id"]
        cart_items = conn.execute("""
            SELECT ci.id as cart_item_id, ci.quantity, ci.variant_id, ci.variant_name,
                   p.id as product_id, p.name, p.regular_price, p.sale_price,
                   pv.name as pv_name, pv.regular_price as pv_reg, pv.sale_price as pv_sale
            FROM cart_items ci
            JOIN products p ON ci.product_id = p.id
            LEFT JOIN product_variants pv ON ci.variant_id = pv.id
            WHERE ci.cart_id = ? AND p.status = 'active'
        """, (cart_id,)).fetchall()

        if not cart_items:
            raise HTTPException(status_code=400, detail="Keranjang belanja kosong atau produk tidak aktif")

        subtotal = 0
        order_items_data = []
        for ci in cart_items:
            # Check if variant price applies
            if ci["variant_id"] and ci["pv_reg"]:
                price = ci["pv_sale"] if ci["pv_sale"] else ci["pv_reg"]
                item_name = f"{ci['name']} ({ci['variant_name']})"
            else:
                price = ci["sale_price"] if ci["sale_price"] else ci["regular_price"]
                item_name = ci["name"]

            line_total = price * ci["quantity"]
            subtotal += line_total
            order_items_data.append({
                "product_id": ci["product_id"],
                "variant_id": ci["variant_id"],
                "variant_name": ci["variant_name"],
                "name": item_name,
                "price": price,
                "quantity": ci["quantity"],
                "subtotal": line_total
            })

        discount_amount = 0
        voucher_id = None
        voucher_code = None

        if payload.voucher_code:
            v_code = payload.voucher_code.strip().upper()
            v = conn.execute("SELECT * FROM vouchers WHERE code = ? AND is_active = 1", (v_code,)).fetchone()
            if v and (v["usage_limit"] == 0 or v["times_used"] < v["usage_limit"]) and (subtotal >= v["min_order_amount"]):
                voucher_id = v["id"]
                voucher_code = v["code"]
                if v["discount_type"] == "percentage":
                    discount_amount = int((subtotal * v["discount_value"]) / 100)
                    if v["max_discount"] > 0 and discount_amount > v["max_discount"]:
                        discount_amount = v["max_discount"]
                else:
                    discount_amount = min(v["discount_value"], subtotal)
                conn.execute("UPDATE vouchers SET times_used = times_used + 1 WHERE id = ?", (v["id"],))

        total_amount = max(0, subtotal - discount_amount)

        now_str = datetime.datetime.now().strftime("%Y%m%d")
        rand_suffix = secrets.token_hex(2).upper()
        order_number = f"PRM-{now_str}-{rand_suffix}"

        cursor = conn.execute("""
            INSERT INTO orders (
                order_number, user_id, customer_name, customer_email, customer_phone,
                subtotal, discount_amount, tax_amount, total_amount, payment_method,
                payment_status, fulfillment_status, voucher_id, voucher_code, internal_notes, ip_address
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'PENDING', 'PENDING', ?, ?, ?, ?)
        """, (
            order_number, user["id"] if user else None, payload.customer_name.strip(),
            payload.customer_email.strip().lower(), payload.customer_phone.strip() if payload.customer_phone else None,
            subtotal, discount_amount, total_amount, payload.payment_method,
            voucher_id, voucher_code, payload.notes, client_ip
        ))
        order_id = cursor.lastrowid

        for item in order_items_data:
            conn.execute("""
                INSERT INTO order_items (order_id, product_id, variant_id, variant_name, product_name, price, quantity, subtotal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (order_id, item["product_id"], item["variant_id"], item["variant_name"], item["name"], item["price"], item["quantity"], item["subtotal"]))

        tx_id = f"TX-{order_number}-{secrets.token_hex(3).upper()}"
        conn.execute("""
            INSERT INTO payments (order_id, transaction_id, gateway, payment_type, amount, status)
            VALUES (?, ?, 'midtrans_simulation', ?, ?, 'PENDING')
        """, (order_id, tx_id, payload.payment_method, total_amount))

        conn.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart_id,))

        log_audit(user["id"] if user else None, payload.customer_email, "ORDER_CREATED", "orders", str(order_id), f"Pesanan dibuat #{order_number} sebesar Rp {total_amount:,}", client_ip, conn=conn)

    return {
        "status": "success",
        "order_number": order_number,
        "total_amount": total_amount,
        "payment_method": payload.payment_method
    }

@router.get("/api/orders/{order_number}/status")
def get_order_status(order_number: str):
    with get_db() as conn:
        row = conn.execute("SELECT payment_status, fulfillment_status FROM orders WHERE order_number = ?", (order_number,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        return dict(row)
