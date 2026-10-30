import os
from fastapi import FastAPI, Request, status, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from app.config import STATIC_DIR, UPLOAD_DIR, APP_DIR
from app.database import init_db, get_setting, get_all_settings
from app.storage import get_fallback_banner
from app.routers import (
    auth,
    storefront,
    orders,
    payments,
    admin,
    admin_products,
    admin_categories,
    admin_orders,
    admin_customers,
    admin_vouchers,
    admin_settings,
)

app = FastAPI(
    title="PRIME APPS — Webstore Digital Premium",
    description="Full-Stack Production-Ready Digital Webstore & Admin Backoffice",
    version="1.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Image Serving with Auto-Fallback (guarantees 200 OK even if an image is missing on disk)
@app.get("/uploads/{filename}", include_in_schema=False)
async def serve_upload_image(filename: str):
    file_path = UPLOAD_DIR / filename
    if file_path.is_file():
        return FileResponse(file_path)
    return Response(content=get_fallback_banner(filename), media_type="image/jpeg")

@app.get("/static/uploads/{filename}", include_in_schema=False)
async def serve_static_upload_image(filename: str):
    file_path = UPLOAD_DIR / filename
    if file_path.is_file():
        return FileResponse(file_path)
    return Response(content=get_fallback_banner(filename), media_type="image/jpeg")

# Mount Static Files & Uploads
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

# Maintenance Mode Middleware
@app.middleware("http")
async def maintenance_middleware(request: Request, call_next):
    path = request.url.path
    # Bypass maintenance for static assets, uploads, admin portal, auth, or health check
    if (
        path.startswith("/static") or
        path.startswith("/uploads") or
        path.startswith("/admin") or
        path.startswith("/api/auth") or
        path.startswith("/api/docs") or
        path == "/robots.txt" or
        path == "/favicon.ico"
    ):
        return await call_next(request)

    # Check maintenance setting
    is_maintenance = get_setting("maintenance_mode", "0")
    if is_maintenance == "1":
        settings = get_all_settings()
        html = f"""
        <!DOCTYPE html>
        <html lang="id">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>{settings.get('store_name', 'PRIME APPS')} — Sedang Pemeliharaan</title>
          <link rel="icon" type="image/svg+xml" href="/static/img/favicon.svg">
          <link rel="stylesheet" href="/static/css/style.css">
        </head>
        <body style="display:flex; align-items:center; justify-content:center; min-height:100vh; text-align:center; padding:20px;">
          <div style="background:var(--bg-surface); padding:48px 36px; border-radius:24px; border:1px solid var(--border-subtle); max-width:520px; box-shadow:var(--shadow-lg);">
            <div style="font-size:3.5rem; margin-bottom:16px;">⚙️</div>
            <h1 style="font-size:1.8rem; margin-bottom:12px;">Sistem Sedang Pemeliharaan</h1>
            <p style="color:var(--text-secondary); line-height:1.6; margin-bottom:24px;">
              Toko sedang melakukan pembaruan katalog lisensi digital. Kami akan segera kembali beroperasi normal dalam beberapa saat.
            </p>
            <div style="font-size:0.85rem; color:var(--text-muted);">
              Butuh bantuan mendesak? Hubungi WhatsApp: <strong>{settings.get('contact_whatsapp', '+62 812-3456-7890')}</strong>
            </div>
            <div style="margin-top:24px; padding-top:16px; border-top:1px solid var(--border-subtle);">
              <a href="/admin/login" style="font-size:0.75rem; color:var(--text-muted);">Akses Administrator</a>
            </div>
          </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html, status_code=503)

    return await call_next(request)

# Favicon Endpoint
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    fav_path = STATIC_DIR / "img" / "favicon.svg"
    if fav_path.exists():
        return FileResponse(fav_path, media_type="image/svg+xml")
    return Response(status_code=204)

# Custom 404 Handler
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"status": "error", "detail": "Endpoint tidak ditemukan"}, status_code=404)
    settings = get_all_settings()
    return templates.TemplateResponse("storefront/404.html", {
        "request": request,
        "store_settings": settings,
        "current_user": None
    }, status_code=404)

# Initialize Database on Startup
@app.on_event("startup")
def on_startup():
    init_db()

# Include Routers
app.include_router(auth.router)
app.include_router(storefront.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(admin.router)
app.include_router(admin_products.router)
app.include_router(admin_categories.router)
app.include_router(admin_orders.router)
app.include_router(admin_customers.router)
app.include_router(admin_vouchers.router)
app.include_router(admin_settings.router)
