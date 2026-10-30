import json
import re
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Request, Depends, HTTPException, Query, UploadFile, File, Form, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app.config import APP_DIR
from app.database import get_db, get_all_settings, log_audit
from app.models import ProductCreateRequest, ProductUpdateRequest
from app.security import require_admin
from app.storage import validate_image_file, save_product_image, delete_product_image

router = APIRouter(tags=["Admin Products"])
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

class ProductStatusUpdate(BaseModel):
    status: str

@router.get("/admin/products", response_class=HTMLResponse)
def list_products_view(
    request: Request,
    q: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    admin: dict = Depends(require_admin)
):
    settings = get_all_settings()
    with get_db() as conn:
        base_where = "WHERE 1=1"
        params = []
        if q:
            base_where += " AND (p.name LIKE ? OR p.sku LIKE ?)"
            params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])
        if status:
            base_where += " AND p.status = ?"
            params.append(status)

        count_query = f"SELECT COUNT(*) as cnt FROM products p {base_where}"
        total_count = conn.execute(count_query, params).fetchone()["cnt"]

        total_pages = max(1, (total_count + per_page - 1) // per_page)
        offset = (page - 1) * per_page

        query = f"""
            SELECT p.*, c.name as category_name,
                   (SELECT COUNT(*) FROM license_keys WHERE product_id = p.id AND is_used = 0) as stock_keys,
                   (SELECT COUNT(*) FROM product_variants WHERE product_id = p.id) as variants_count,
                   (SELECT image_url FROM product_images WHERE product_id = p.id ORDER BY is_primary DESC, display_order ASC LIMIT 1) as primary_image
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            {base_where}
            ORDER BY p.id DESC
            LIMIT ? OFFSET ?
        """
        rows = conn.execute(query, params + [per_page, offset]).fetchall()

    ctx = {
        "request": request,
        "current_admin": admin,
        "store_settings": settings,
        "active_nav": "products",
        "products": [dict(r) for r in rows],
        "query_q": q or "",
        "query_status": status or "",
        "page": page,
        "per_page": per_page,
        "total_count": total_count,
        "total_pages": total_pages
    }
    return templates.TemplateResponse("admin/products.html", ctx)

@router.get("/admin/products/new", response_class=HTMLResponse)
def new_product_view(request: Request, admin: dict = Depends(require_admin)):
    settings = get_all_settings()
    with get_db() as conn:
        categories = conn.execute("SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name ASC").fetchall()
        brands = conn.execute("SELECT id, name FROM brands WHERE is_active = 1 ORDER BY name ASC").fetchall()

    ctx = {
        "request": request,
        "current_admin": admin,
        "store_settings": settings,
        "active_nav": "products",
        "product": None,
        "images": [],
        "variants": [],
        "categories": [dict(c) for c in categories],
        "brands": [dict(b) for b in brands],
        "features_text": "",
        "stock_keys_count": 0
    }
    return templates.TemplateResponse("admin/product_form.html", ctx)

@router.get("/admin/products/{product_id}/edit", response_class=HTMLResponse)
def edit_product_view(product_id: int, request: Request, admin: dict = Depends(require_admin)):
    settings = get_all_settings()
    with get_db() as conn:
        prod = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if not prod:
            raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

        categories = conn.execute("SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name ASC").fetchall()
        brands = conn.execute("SELECT id, name FROM brands WHERE is_active = 1 ORDER BY name ASC").fetchall()

        images = conn.execute("SELECT * FROM product_images WHERE product_id = ? ORDER BY is_primary DESC, display_order ASC, id ASC", (product_id,)).fetchall()
        variants = conn.execute("SELECT * FROM product_variants WHERE product_id = ? ORDER BY sort_order ASC, id ASC", (product_id,)).fetchall()
        stock_cnt = conn.execute("SELECT COUNT(*) as cnt FROM license_keys WHERE product_id = ? AND is_used = 0", (product_id,)).fetchone()["cnt"]

    features_list = []
    if prod["features_json"]:
        try:
            features_list = json.loads(prod["features_json"])
        except Exception:
            features_list = []

    ctx = {
        "request": request,
        "current_admin": admin,
        "store_settings": settings,
        "active_nav": "products",
        "product": dict(prod),
        "images": [dict(img) for img in images],
        "variants": [dict(v) for v in variants],
        "categories": [dict(c) for c in categories],
        "brands": [dict(b) for b in brands],
        "features_text": "\n".join(features_list),
        "stock_keys_count": stock_cnt
    }
    return templates.TemplateResponse("admin/product_form.html", ctx)

# API ENDPOINTS
@router.patch("/api/admin/products/{product_id}/status")
def update_product_status(product_id: int, payload: ProductStatusUpdate, request: Request, admin: dict = Depends(require_admin)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    with get_db() as conn:
        prod = conn.execute("SELECT id, name FROM products WHERE id = ?", (product_id,)).fetchone()
        if not prod:
            raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
        conn.execute("UPDATE products SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (payload.status, product_id))

    log_audit(admin["id"], admin["email"], "PRODUCT_STATUS_TOGGLED", "products", str(product_id), f"Status produk '{prod['name']}' diubah menjadi {payload.status}", client_ip)
    return {"status": "success", "new_status": payload.status}

@router.post("/api/admin/products")
def create_product(payload: ProductCreateRequest, request: Request, admin: dict = Depends(require_admin)):
    slug = payload.slug.strip() if payload.slug else slugify(payload.name)
    features_json = json.dumps(payload.features or [])
    client_ip = request.client.host if request.client else "127.0.0.1"

    with get_db() as conn:
        existing = conn.execute("SELECT id FROM products WHERE slug = ?", (slug,)).fetchone()
        if existing:
            slug = f"{slug}-{uuid_short()}"

        cursor = conn.execute("""
            INSERT INTO products (
                name, slug, category_id, brand_id, sku, short_description, description,
                features_json, regular_price, sale_price, is_featured, is_trending,
                status, delivery_type, delivery_instructions, seo_title, seo_description, sort_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payload.name, slug, payload.category_id, payload.brand_id, payload.sku,
            payload.short_description, payload.description, features_json,
            payload.regular_price, payload.sale_price, 1 if payload.is_featured else 0,
            1 if payload.is_trending else 0, payload.status, payload.delivery_type,
            payload.delivery_instructions, payload.seo_title, payload.seo_description, payload.sort_order
        ))
        product_id = cursor.lastrowid

        # Insert variants if provided
        if payload.variants:
            for idx, v in enumerate(payload.variants):
                v_name = v.get("name", "").strip()
                if v_name:
                    v_reg = int(v.get("regular_price") or payload.regular_price)
                    v_sale = int(v.get("sale_price")) if v.get("sale_price") is not None and str(v.get("sale_price")).strip() else None
                    v_sku = v.get("sku", "")
                    conn.execute("""
                        INSERT INTO product_variants (product_id, name, regular_price, sale_price, sku, sort_order, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                    """, (product_id, v_name, v_reg, v_sale, v_sku, idx))

        if payload.license_keys:
            for lk in payload.license_keys:
                code = lk.strip()
                if code:
                    conn.execute("INSERT INTO license_keys (product_id, license_code) VALUES (?, ?)", (product_id, code))

    log_audit(admin["id"], admin["email"], "PRODUCT_CREATED", "products", str(product_id), f"Membuat produk: {payload.name}", client_ip)
    return {"status": "success", "id": product_id, "slug": slug}

@router.put("/api/admin/products/{product_id}")
def update_product(product_id: int, payload: ProductCreateRequest, request: Request, admin: dict = Depends(require_admin)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    slug = payload.slug.strip() if payload.slug else slugify(payload.name)
    features_json = json.dumps(payload.features or [])

    with get_db() as conn:
        prod = conn.execute("SELECT id FROM products WHERE id = ?", (product_id,)).fetchone()
        if not prod:
            raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

        conn.execute("""
            UPDATE products SET
                name = ?, slug = ?, category_id = ?, brand_id = ?, sku = ?,
                short_description = ?, description = ?, features_json = ?,
                regular_price = ?, sale_price = ?, is_featured = ?, is_trending = ?,
                status = ?, delivery_type = ?, delivery_instructions = ?,
                seo_title = ?, seo_description = ?, sort_order = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            payload.name, slug, payload.category_id, payload.brand_id, payload.sku,
            payload.short_description, payload.description, features_json,
            payload.regular_price, payload.sale_price, 1 if payload.is_featured else 0,
            1 if payload.is_trending else 0, payload.status, payload.delivery_type,
            payload.delivery_instructions, payload.seo_title, payload.seo_description, payload.sort_order,
            product_id
        ))

        # Update variants
        if payload.variants is not None:
            conn.execute("DELETE FROM product_variants WHERE product_id = ?", (product_id,))
            for idx, v in enumerate(payload.variants):
                v_name = v.get("name", "").strip()
                if v_name:
                    v_reg = int(v.get("regular_price") or payload.regular_price)
                    v_sale = int(v.get("sale_price")) if v.get("sale_price") is not None and str(v.get("sale_price")).strip() else None
                    v_sku = v.get("sku", "")
                    conn.execute("""
                        INSERT INTO product_variants (product_id, name, regular_price, sale_price, sku, sort_order, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                    """, (product_id, v_name, v_reg, v_sale, v_sku, idx))

        if payload.license_keys:
            for lk in payload.license_keys:
                code = lk.strip()
                if code:
                    conn.execute("INSERT INTO license_keys (product_id, license_code) VALUES (?, ?)", (product_id, code))

    log_audit(admin["id"], admin["email"], "PRODUCT_UPDATED", "products", str(product_id), f"Memperbarui produk: {payload.name}", client_ip)
    return {"status": "success", "id": product_id}

@router.delete("/api/admin/products/{product_id}")
def delete_product(product_id: int, request: Request, admin: dict = Depends(require_admin)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    with get_db() as conn:
        prod = conn.execute("SELECT name FROM products WHERE id = ?", (product_id,)).fetchone()
        if not prod:
            raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

        images = conn.execute("SELECT id FROM product_images WHERE product_id = ?", (product_id,)).fetchall()
        for img in images:
            delete_product_image(img["id"], product_id)

        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))

    log_audit(admin["id"], admin["email"], "PRODUCT_DELETED", "products", str(product_id), f"Menghapus produk: {prod['name']}", client_ip)
    return {"status": "success", "message": "Produk berhasil dihapus"}

# Image Upload Endpoints
@router.post("/api/admin/products/{product_id}/images")
async def upload_product_image_endpoint(
    product_id: int,
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(""),
    admin: dict = Depends(require_admin)
):
    content = await file.read()
    validate_image_file(file, content)

    with get_db() as conn:
        prod = conn.execute("SELECT id, name FROM products WHERE id = ?", (product_id,)).fetchone()
        if not prod:
            raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

    saved = save_product_image(
        file_bytes=content,
        original_filename=file.filename or "product.jpg",
        product_id=product_id,
        alt_text=alt_text or prod["name"]
    )
    return saved

@router.delete("/api/admin/products/{product_id}/images/{image_id}")
def delete_image_endpoint(product_id: int, image_id: int, admin: dict = Depends(require_admin)):
    ok = delete_product_image(image_id, product_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Foto tidak ditemukan")
    return {"status": "success", "message": "Foto berhasil dihapus"}

@router.post("/api/admin/products/{product_id}/images/{image_id}/primary")
def set_primary_image_endpoint(product_id: int, image_id: int, admin: dict = Depends(require_admin)):
    with get_db() as conn:
        conn.execute("UPDATE product_images SET is_primary = 0 WHERE product_id = ?", (product_id,))
        conn.execute("UPDATE product_images SET is_primary = 1 WHERE id = ? AND product_id = ?", (image_id, product_id))
    return {"status": "success"}

def uuid_short() -> str:
    import secrets
    return secrets.token_hex(3)
