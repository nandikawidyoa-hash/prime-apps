import json
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.config import APP_DIR
from app.database import get_db, get_all_settings
from app.security import get_current_user_optional, get_current_user_required

router = APIRouter()
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

def get_common_context(request: Request) -> dict:
    settings = get_all_settings()
    user = get_current_user_optional(request)
    return {
        "request": request,
        "store_settings": settings,
        "current_user": user
    }

@router.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    ctx = get_common_context(request)
    with get_db() as conn:
        categories = conn.execute("""
            SELECT id, name, slug, icon, display_order 
            FROM categories 
            WHERE is_active = 1 
            ORDER BY display_order ASC, name ASC
        """).fetchall()

        featured_rows = conn.execute("""
            SELECT p.*, c.name as category_name,
                   (SELECT image_url FROM product_images WHERE product_id = p.id ORDER BY is_primary DESC, display_order ASC LIMIT 1) as primary_image
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.status = 'active' AND p.is_featured = 1
            ORDER BY p.sort_order ASC, p.id DESC
            LIMIT 8
        """).fetchall()

        latest_rows = conn.execute("""
            SELECT p.*, c.name as category_name,
                   (SELECT image_url FROM product_images WHERE product_id = p.id ORDER BY is_primary DESC, display_order ASC LIMIT 1) as primary_image
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.status = 'active'
            ORDER BY p.id DESC
            LIMIT 8
        """).fetchall()

    ctx.update({
        "categories": [dict(c) for c in categories],
        "featured_products": [dict(p) for p in featured_rows],
        "latest_products": [dict(p) for p in latest_rows]
    })
    return templates.TemplateResponse("storefront/index.html", ctx)

@router.get("/catalog", response_class=HTMLResponse)
def catalog_page(
    request: Request,
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    sort: Optional[str] = Query("newest"),
    featured: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(9, ge=1, le=50)
):
    ctx = get_common_context(request)
    
    with get_db() as conn:
        categories = conn.execute("SELECT id, name, slug, icon FROM categories WHERE is_active = 1 ORDER BY display_order ASC").fetchall()

        base_where = "WHERE p.status = 'active'"
        params = []

        if q:
            base_where += " AND (p.name LIKE ? OR p.short_description LIKE ? OR p.description LIKE ? OR p.sku LIKE ?)"
            term = f"%{q.strip()}%"
            params.extend([term, term, term, term])

        if category:
            base_where += " AND c.slug = ?"
            params.append(category)

        if featured:
            base_where += " AND p.is_featured = 1"

        count_query = f"SELECT COUNT(*) as cnt FROM products p LEFT JOIN categories c ON p.category_id = c.id {base_where}"
        total_count = conn.execute(count_query, params).fetchone()["cnt"]

        total_pages = max(1, (total_count + per_page - 1) // per_page)
        offset = (page - 1) * per_page

        order_by = "ORDER BY p.id DESC"
        if sort == "popular":
            order_by = "ORDER BY p.is_trending DESC, p.is_featured DESC, p.sort_order ASC, p.id DESC"
        elif sort == "price_asc":
            order_by = "ORDER BY COALESCE(p.sale_price, p.regular_price) ASC"
        elif sort == "price_desc":
            order_by = "ORDER BY COALESCE(p.sale_price, p.regular_price) DESC"

        query = f"""
            SELECT p.*, c.name as category_name, c.slug as category_slug,
                   (SELECT image_url FROM product_images WHERE product_id = p.id ORDER BY is_primary DESC, display_order ASC LIMIT 1) as primary_image
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            {base_where}
            {order_by}
            LIMIT ? OFFSET ?
        """
        products = conn.execute(query, params + [per_page, offset]).fetchall()

    ctx.update({
        "categories": [dict(c) for c in categories],
        "products": [dict(p) for p in products],
        "query_search": q or "",
        "selected_category": category or "",
        "selected_sort": sort or "newest",
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages
    })
    return templates.TemplateResponse("storefront/catalog.html", ctx)

@router.get("/product/{slug}", response_class=HTMLResponse)
def product_detail(request: Request, slug: str):
    ctx = get_common_context(request)

    with get_db() as conn:
        prod = conn.execute("""
            SELECT p.*, c.name as category_name, c.slug as category_slug, b.name as brand_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            WHERE p.slug = ? AND p.status = 'active'
        """, (slug,)).fetchone()

        if not prod:
            raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

        product_id = prod["id"]

        images = conn.execute("""
            SELECT id, image_url, thumbnail_url, alt_text, is_primary 
            FROM product_images 
            WHERE product_id = ? 
            ORDER BY is_primary DESC, display_order ASC, id ASC
        """, (product_id,)).fetchall()

        variants = conn.execute("""
            SELECT id, name, regular_price, sale_price, sku 
            FROM product_variants 
            WHERE product_id = ? AND is_active = 1 
            ORDER BY sort_order ASC, id ASC
        """, (product_id,)).fetchall()

        stock = conn.execute("""
            SELECT COUNT(*) as count FROM license_keys WHERE product_id = ? AND is_used = 0
        """, (product_id,)).fetchone()

        related = conn.execute("""
            SELECT p.*, c.name as category_name,
                   (SELECT image_url FROM product_images WHERE product_id = p.id ORDER BY is_primary DESC LIMIT 1) as primary_image
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.status = 'active' AND p.id != ? AND (p.category_id = ? OR p.category_id IS NULL)
            LIMIT 4
        """, (product_id, prod["category_id"])).fetchall()

    prod_dict = dict(prod)
    prod_dict["stock_count"] = stock["count"] if stock else 0

    features = []
    if prod["features_json"]:
        try:
            features = json.loads(prod["features_json"])
        except Exception:
            features = []

    ctx.update({
        "product": prod_dict,
        "images": [dict(img) for img in images],
        "variants": [dict(v) for v in variants],
        "features": features,
        "related_products": [dict(r) for r in related]
    })
    return templates.TemplateResponse("storefront/product.html", ctx)

@router.get("/cart", response_class=HTMLResponse)
def cart_page(request: Request):
    ctx = get_common_context(request)
    session_id = request.cookies.get("cart_session_id")
    user = ctx["current_user"]

    items = []
    subtotal = 0
    with get_db() as conn:
        cart_row = None
        if user:
            cart_row = conn.execute("SELECT id FROM carts WHERE user_id = ?", (user["id"],)).fetchone()
        elif session_id:
            cart_row = conn.execute("SELECT id FROM carts WHERE session_id = ?", (session_id,)).fetchone()

        if cart_row:
            cart_id = cart_row["id"]
            rows = conn.execute("""
                SELECT ci.id as cart_item_id, ci.quantity, ci.variant_id, ci.variant_name,
                       p.id as product_id, p.name, p.slug,
                       COALESCE(pv.sale_price, pv.regular_price, p.sale_price, p.regular_price) as price,
                       (SELECT image_url FROM product_images WHERE product_id = p.id ORDER BY is_primary DESC LIMIT 1) as image_url
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.id
                LEFT JOIN product_variants pv ON ci.variant_id = pv.id
                WHERE ci.cart_id = ?
            """, (cart_id,)).fetchall()

            for r in rows:
                item_dict = dict(r)
                if item_dict.get("variant_name"):
                    item_dict["name"] = f"{item_dict['name']} ({item_dict['variant_name']})"
                item_dict["subtotal"] = item_dict["price"] * item_dict["quantity"]
                subtotal += item_dict["subtotal"]
                items.append(item_dict)

    ctx.update({
        "items": items,
        "subtotal": subtotal,
        "discount_amount": 0,
        "total_amount": subtotal,
        "applied_voucher": None
    })
    return templates.TemplateResponse("storefront/cart.html", ctx)

@router.get("/checkout", response_class=HTMLResponse)
def checkout_page(
    request: Request,
    instant_product_id: Optional[int] = Query(None),
    instant_variant_id: Optional[int] = Query(None)
):
    ctx = get_common_context(request)
    user = ctx["current_user"]
    session_id = request.cookies.get("cart_session_id")

    items = []
    subtotal = 0

    with get_db() as conn:
        if instant_product_id:
            prod = conn.execute("SELECT id, name, slug, regular_price, sale_price FROM products WHERE id = ? AND status = 'active'", (instant_product_id,)).fetchone()
            if prod:
                var_name = None
                price = prod["sale_price"] if prod["sale_price"] else prod["regular_price"]
                if instant_variant_id:
                    v_row = conn.execute("SELECT name, regular_price, sale_price FROM product_variants WHERE id = ? AND product_id = ?", (instant_variant_id, instant_product_id)).fetchone()
                    if v_row:
                        var_name = v_row["name"]
                        price = v_row["sale_price"] if v_row["sale_price"] else v_row["regular_price"]

                item_name = f"{prod['name']} ({var_name})" if var_name else prod["name"]
                items.append({
                    "product_id": prod["id"],
                    "variant_id": instant_variant_id,
                    "variant_name": var_name,
                    "name": item_name,
                    "slug": prod["slug"],
                    "price": price,
                    "quantity": 1,
                    "subtotal": price
                })
                subtotal = price
        else:
            cart_row = None
            if user:
                cart_row = conn.execute("SELECT id FROM carts WHERE user_id = ?", (user["id"],)).fetchone()
            elif session_id:
                cart_row = conn.execute("SELECT id FROM carts WHERE session_id = ?", (session_id,)).fetchone()

            if cart_row:
                rows = conn.execute("""
                    SELECT ci.id as cart_item_id, ci.quantity, ci.variant_id, ci.variant_name,
                           p.id as product_id, p.name, p.slug,
                           COALESCE(pv.sale_price, pv.regular_price, p.sale_price, p.regular_price) as price
                    FROM cart_items ci
                    JOIN products p ON ci.product_id = p.id
                    LEFT JOIN product_variants pv ON ci.variant_id = pv.id
                    WHERE ci.cart_id = ?
                """, (cart_row["id"],)).fetchall()

                for r in rows:
                    item_dict = dict(r)
                    if item_dict.get("variant_name"):
                        item_dict["name"] = f"{item_dict['name']} ({item_dict['variant_name']})"
                    item_dict["subtotal"] = item_dict["price"] * item_dict["quantity"]
                    subtotal += item_dict["subtotal"]
                    items.append(item_dict)

    if not items:
        return RedirectResponse("/cart", status_code=302)

    ctx.update({
        "items": items,
        "subtotal": subtotal,
        "discount_amount": 0,
        "total_amount": subtotal
    })
    return templates.TemplateResponse("storefront/checkout.html", ctx)

@router.get("/payment/{order_number}", response_class=HTMLResponse)
def payment_page(request: Request, order_number: str):
    ctx = get_common_context(request)

    with get_db() as conn:
        order = conn.execute("SELECT * FROM orders WHERE order_number = ?", (order_number,)).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")

        if order["payment_status"] == "PAID":
            return RedirectResponse(f"/order/{order_number}/success", status_code=302)

        payment = conn.execute("SELECT * FROM payments WHERE order_id = ?", (order["id"],)).fetchone()

    ctx.update({
        "order": dict(order),
        "payment": dict(payment) if payment else None
    })
    return templates.TemplateResponse("storefront/payment.html", ctx)

@router.get("/order/{order_number}/success", response_class=HTMLResponse)
def order_success_page(request: Request, order_number: str):
    ctx = get_common_context(request)

    with get_db() as conn:
        order = conn.execute("SELECT * FROM orders WHERE order_number = ?", (order_number,)).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Pesanan tidak ditemukan")

        items = conn.execute("""
            SELECT id, product_name, price, quantity, subtotal, digital_payload 
            FROM order_items 
            WHERE order_id = ?
        """, (order["id"],)).fetchall()

    ctx.update({
        "order": dict(order),
        "items": [dict(i) for i in items]
    })
    return templates.TemplateResponse("storefront/order_success.html", ctx)

@router.get("/account", response_class=HTMLResponse)
def account_page(request: Request, user: dict = Depends(get_current_user_required)):
    ctx = get_common_context(request)

    with get_db() as conn:
        orders_raw = conn.execute("""
            SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC
        """, (user["id"],)).fetchall()

        orders_list = []
        for o in orders_raw:
            o_dict = dict(o)
            items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (o["id"],)).fetchall()
            o_dict["items"] = [dict(i) for i in items]
            orders_list.append(o_dict)

    ctx.update({
        "orders": orders_list
    })
    return templates.TemplateResponse("storefront/account.html", ctx)

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    ctx = get_common_context(request)
    if ctx["current_user"]:
        return RedirectResponse("/account", status_code=302)
    return templates.TemplateResponse("storefront/login.html", ctx)

@router.get("/faq", response_class=HTMLResponse)
def faq_page(request: Request):
    return templates.TemplateResponse("storefront/faq.html", get_common_context(request))

@router.get("/about", response_class=HTMLResponse)
def about_page(request: Request):
    return templates.TemplateResponse("storefront/about.html", get_common_context(request))

@router.get("/terms", response_class=HTMLResponse)
def terms_page(request: Request):
    return templates.TemplateResponse("storefront/terms.html", get_common_context(request))

@router.get("/privacy", response_class=HTMLResponse)
def privacy_page(request: Request):
    return templates.TemplateResponse("storefront/privacy.html", get_common_context(request))

@router.get("/refund", response_class=HTMLResponse)
def refund_page(request: Request):
    return templates.TemplateResponse("storefront/refund.html", get_common_context(request))

@router.get("/contact", response_class=HTMLResponse)
def contact_page(request: Request):
    return templates.TemplateResponse("storefront/contact.html", get_common_context(request))

@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return "User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\nSitemap: /sitemap.xml\n"

@router.get("/sitemap.xml")
def sitemap_xml():
    with get_db() as conn:
        products = conn.execute("SELECT slug, updated_at FROM products WHERE status = 'active'").fetchall()
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += '  <url><loc>/</loc><priority>1.0</priority></url>\n'
    xml += '  <url><loc>/catalog</loc><priority>0.8</priority></url>\n'
    xml += '  <url><loc>/faq</loc><priority>0.5</priority></url>\n'
    xml += '  <url><loc>/about</loc><priority>0.5</priority></url>\n'
    for p in products:
        xml += f'  <url><loc>/product/{p["slug"]}</loc><priority>0.9</priority></url>\n'
    xml += '</urlset>'
    return Response(content=xml, media_type="application/xml")
