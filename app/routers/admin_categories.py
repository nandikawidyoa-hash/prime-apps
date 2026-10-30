import re
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import APP_DIR
from app.database import get_db, get_all_settings, log_audit
from app.models import CategoryCreateRequest, BrandCreateRequest
from app.security import require_admin

router = APIRouter(tags=["Admin Categories & Brands"])
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

@router.get("/admin/categories", response_class=HTMLResponse)
def list_categories_view(request: Request, admin: dict = Depends(require_admin)):
    settings = get_all_settings()
    with get_db() as conn:
        categories = conn.execute("SELECT * FROM categories ORDER BY display_order ASC, name ASC").fetchall()
        brands = conn.execute("SELECT * FROM brands ORDER BY name ASC").fetchall()

    ctx = {
        "request": request,
        "current_admin": admin,
        "store_settings": settings,
        "active_nav": "categories",
        "categories": [dict(c) for c in categories],
        "brands": [dict(b) for b in brands]
    }
    return templates.TemplateResponse("admin/categories.html", ctx)

@router.post("/api/admin/categories")
def create_category(payload: CategoryCreateRequest, request: Request, admin: dict = Depends(require_admin)):
    slug = payload.slug.strip() if payload.slug else slugify(payload.name)
    client_ip = request.client.host if request.client else "127.0.0.1"

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO categories (name, slug, description, icon, display_order, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (payload.name.strip(), slug, payload.description, payload.icon or "📦", payload.display_order, 1 if payload.is_active else 0))
        cat_id = cursor.lastrowid

    log_audit(admin["id"], admin["email"], "CATEGORY_CREATED", "categories", str(cat_id), f"Membuat kategori: {payload.name}", client_ip)
    return {"status": "success", "id": cat_id, "slug": slug}

@router.delete("/api/admin/categories/{category_id}")
def delete_category(category_id: int, request: Request, admin: dict = Depends(require_admin)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    with get_db() as conn:
        conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    log_audit(admin["id"], admin["email"], "CATEGORY_DELETED", "categories", str(category_id), "Menghapus kategori", client_ip)
    return {"status": "success"}

@router.post("/api/admin/brands")
def create_brand(payload: BrandCreateRequest, request: Request, admin: dict = Depends(require_admin)):
    slug = payload.slug.strip() if payload.slug else slugify(payload.name)
    client_ip = request.client.host if request.client else "127.0.0.1"

    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO brands (name, slug, logo_url, website, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (payload.name.strip(), slug, payload.logo_url, payload.website, 1 if payload.is_active else 0))
        brand_id = cursor.lastrowid

    log_audit(admin["id"], admin["email"], "BRAND_CREATED", "brands", str(brand_id), f"Membuat brand: {payload.name}", client_ip)
    return {"status": "success", "id": brand_id, "slug": slug}

@router.delete("/api/admin/brands/{brand_id}")
def delete_brand(brand_id: int, request: Request, admin: dict = Depends(require_admin)):
    client_ip = request.client.host if request.client else "127.0.0.1"
    with get_db() as conn:
        conn.execute("DELETE FROM brands WHERE id = ?", (brand_id,))
    log_audit(admin["id"], admin["email"], "BRAND_DELETED", "brands", str(brand_id), "Menghapus brand", client_ip)
    return {"status": "success"}
