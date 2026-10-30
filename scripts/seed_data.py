#!/usr/bin/env python3
"""
Comprehensive database seeder for PRIME APPS webstore.
Populates:
- 3 Exact Price List Categories: Streaming & Movies, Design & Editing, AI & Productivity
- 23 Real Products with exact pricing & variants from official Price List
- High-res generated product banners & thumbnails saved in static/uploads/
- License key stock for instant digital delivery
- Superadmin & Demo Customer accounts
- Promotional vouchers
"""

import os
import sys
import json
import uuid
import datetime
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

bootstrap_path = BASE_DIR / "bootstrap.py"
if bootstrap_path.exists():
    with open(bootstrap_path) as bf:
        exec(bf.read(), globals())

from app.config import UPLOAD_DIR
from app.database import get_db, init_db, set_setting, log_audit
from app.security import hash_password

def generate_product_image(product_id: int, title: str, subtitle: str, color_hex: str, slug: str = "") -> dict:
    """Generates crisp 1280x800 authentic brand logo banner and 400x300 thumbnail using Pillow."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    img_uuid = uuid.uuid4().hex

    width, height = 1280, 800
    img = Image.new("RGB", (width, height), color="#0c0c10")
    draw = ImageDraw.Draw(img)

    bg_styles = {
        "netflix-premium": ("#141414", "#0a0a0a", "#e50914"),
        "hbo-max": ("#1f0a38", "#0d041a", "#9933ff"),
        "disney-plus-hotstar": ("#0c1b33", "#050b17", "#0063e5"),
        "viu-premium": ("#2a2202", "#120e01", "#fcbb00"),
        "vidio-platinum": ("#29080b", "#140405", "#e50914"),
        "wetv-vip": ("#061a24", "#030c12", "#00b464"),
        "amazon-prime-video": ("#0b1a29", "#040b12", "#00a8e1"),
        "bstation-vip": ("#0a1f2e", "#040e14", "#23ade5"),
        "iqiyi-vip": ("#062412", "#021208", "#00c455"),
        "loklok-vip": ("#1c1708", "#0a0802", "#f5a623"),
        "canva-pro": ("#061d2b", "#120826", "#00c4cc"),
        "capcut-pro": ("#141414", "#080808", "#ffffff"),
        "alight-motion": ("#062222", "#031111", "#00e5c9"),
        "meitu-vip": ("#290616", "#14030b", "#ff2a85"),
        "wink-vip": ("#1e092b", "#0d0414", "#a855f7"),
        "picsart-pro": ("#1f0a2e", "#0a0312", "#d946ef"),
        "chatgpt-plus-go": ("#061a15", "#020d0a", "#10a37f"),
        "google-gemini-ai": ("#0d1329", "#060914", "#4f8df5"),
        "zoom-meeting-pro": ("#081938", "#030a17", "#2d8cff"),
        "office-365-onedrive": ("#240e04", "#0f0501", "#eb3c00"),
        "scribd-premium": ("#061d21", "#020d0f", "#1e7b85"),
        "duolingo-super": ("#102904", "#071401", "#58cc02"),
        "camscanner-vip": ("#051f1c", "#020f0d", "#1ba195"),
    }
    c_top, c_bot, accent = bg_styles.get(slug, ("#181820", "#0e0e14", color_hex or "#3b82f6"))

    # Ambient radial glow behind card
    cx, cy = width // 2, height // 2 - 35
    for radius in range(540, 40, -25):
        alpha = int(45 * (radius / 540))
        glow_box = [cx - radius, cy - radius, cx + radius, cy + radius]
        draw.ellipse(glow_box, fill=c_top)

    # Outer Frame Card
    card_x0, card_y0 = 120, 85
    card_x1, card_y1 = width - 120, height - 85
    draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=32, fill=c_bot, outline=accent, width=3)

    # Top Pill Badge
    draw.rounded_rectangle([card_x0 + 50, card_y0 + 40, card_x0 + 260, card_y0 + 82], radius=21, fill=accent)
    draw.text((card_x0 + 72, card_y0 + 52), "PRIME APPS OFFICIAL", fill="#ffffff")

    # Center Logo Dimensions
    icon_size = 230
    ix0 = cx - icon_size // 2
    iy0 = cy - icon_size // 2 - 25
    ix1 = ix0 + icon_size
    iy1 = iy0 + icon_size
    icx, icy = cx, cy - 25

    # Draw specific authentic app logo
    if slug == "netflix-premium":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#000000", outline="#e50914", width=3)
        nw, nh = 36, 140
        nx0, nx1 = icx - 50, icx + 50 - nw
        draw.rectangle([nx0, icy - nh/2, nx0 + nw, icy + nh/2], fill="#b1060f")
        draw.rectangle([nx1, icy - nh/2, nx1 + nw, icy + nh/2], fill="#b1060f")
        draw.polygon([(nx0, icy - nh/2), (nx0 + nw, icy - nh/2), (nx1 + nw, icy + nh/2), (nx1, icy + nh/2)], fill="#e50914")

    elif slug == "canva-pro":
        draw.ellipse([ix0, iy0, ix1, iy1], fill="#00c4cc", outline="#7d2ae8", width=5)
        draw.ellipse([ix0 + 20, iy0 + 20, ix1 - 20, iy1 - 20], fill="#1c0b38")
        draw.arc([icx - 58, icy - 58, icx + 58, icy + 58], start=45, end=315, fill="#00c4cc", width=28)
        draw.ellipse([icx + 22, icy - 48, icx + 48, icy - 22], fill="#7d2ae8")

    elif slug == "capcut-pro":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#000000", outline="#ffffff", width=3)
        draw.polygon([(icx - 70, icy - 50), (icx, icy - 10), (icx - 70, icy + 30)], fill="#ffffff")
        draw.polygon([(icx + 70, icy + 50), (icx, icy + 10), (icx + 70, icy - 30)], fill="#ffffff")
        draw.line([(icx - 70, icy - 10), (icx + 70, icy + 10)], fill="#000000", width=9)

    elif slug == "alight-motion":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#041c1c", outline="#00e5c9", width=3)
        for r in range(25, 80, 12):
            draw.arc([icx - r, icy - r, icx + r, icy + r], start=r*4, end=r*4 + 210, fill="#00e5c9", width=9)

    elif slug == "chatgpt-plus-go":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#10a37f")
        for angle_deg in range(0, 360, 60):
            rad = math.radians(angle_deg)
            px = icx + math.cos(rad) * 34
            py = icy + math.sin(rad) * 34
            draw.arc([px - 36, py - 36, px + 36, py + 36], start=angle_deg, end=angle_deg + 210, fill="#ffffff", width=8)

    elif slug == "google-gemini-ai":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#13172e", outline="#4f8df5", width=3)
        points = [
            (icx, icy - 80), (icx + 18, icy - 22),
            (icx + 80, icy), (icx + 18, icy + 22),
            (icx, icy + 80), (icx - 18, icy + 22),
            (icx - 80, icy), (icx - 18, icy - 22)
        ]
        draw.polygon(points, fill="#4f8df5")
        draw.polygon([(icx, icy - 48), (icx + 11, icy - 11), (icx + 48, icy), (icx + 11, icy + 11), (icx, icy + 48), (icx - 11, icy + 11), (icx - 48, icy), (icx - 11, icy - 11)], fill="#ffffff")

    elif slug == "zoom-meeting-pro":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#2d8cff")
        cw, ch = 90, 60
        draw.rounded_rectangle([icx - 52, icy - ch/2, icx - 52 + cw, icy + ch/2], radius=16, fill="#ffffff")
        draw.polygon([(icx + 45, icy - 9), (icx + 78, icy - 28), (icx + 78, icy + 28), (icx + 45, icy + 9)], fill="#ffffff")

    elif slug == "duolingo-super":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#58cc02")
        eye_r = 36
        draw.ellipse([icx - 58 - eye_r, icy - 25 - eye_r, icx - 58 + eye_r, icy - 25 + eye_r], fill="#ffffff")
        draw.ellipse([icx - 58 - 15, icy - 25 - 15, icx - 58 + 15, icy - 25 + 15], fill="#4b4b4b")
        draw.ellipse([icx + 58 - eye_r, icy - 25 - eye_r, icx + 58 + eye_r, icy - 25 + eye_r], fill="#ffffff")
        draw.ellipse([icx + 58 - 15, icy - 25 - 15, icx + 58 + 15, icy - 25 + 15], fill="#4b4b4b")
        draw.polygon([(icx - 24, icy + 12), (icx + 24, icy + 12), (icx, icy + 48)], fill="#ff9600")

    elif slug == "disney-plus-hotstar":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#041226", outline="#0063e5", width=3)
        draw.arc([icx - 90, icy - 70, icx + 90, icy + 70], start=180, end=350, fill="#ffffff", width=9)
        draw.line([(icx + 40, icy - 32), (icx + 40, icy + 32)], fill="#0063e5", width=11)
        draw.line([(icx + 8, icy), (icx + 72, icy)], fill="#0063e5", width=11)
        draw.text((icx - 60, icy - 15), "Disney+", fill="#ffffff")

    elif slug == "hbo-max":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#2b0d4f", outline="#9933ff", width=3)
        draw.ellipse([icx - 52, icy - 52, icx + 52, icy + 52], fill="#9933ff")
        draw.ellipse([icx - 24, icy - 24, icx + 24, icy + 24], fill="#ffffff")
        draw.text((icx - 38, icy + 58), "MAX", fill="#ffffff")

    elif slug == "viu-premium":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#fcbb00")
        draw.ellipse([icx - 32, icy - 32, icx + 32, icy + 32], fill="#000000")
        draw.ellipse([icx - 15, icy - 15, icx + 15, icy + 15], fill="#fcbb00")
        draw.text((icx - 26, icy + 44), "VIU", fill="#000000")

    elif slug == "vidio-platinum":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#e50914")
        draw.polygon([(icx - 32, icy - 52), (icx + 50, icy), (icx - 32, icy + 52)], fill="#ffffff")

    elif slug == "amazon-prime-video":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#0b1a29", outline="#00a8e1", width=3)
        draw.text((icx - 68, icy - 32), "prime", fill="#ffffff")
        draw.arc([icx - 65, icy - 10, icx + 65, icy + 42], start=20, end=160, fill="#00a8e1", width=9)

    elif slug == "wetv-vip":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#081f2b", outline="#00b464", width=3)
        draw.polygon([(icx - 48, icy - 42), (icx + 38, icy), (icx - 48, icy + 42)], fill="#00b464")
        draw.polygon([(icx - 22, icy - 26), (icx + 54, icy), (icx - 22, icy + 26)], fill="#ff8c00")

    elif slug == "bstation-vip":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#23ade5")
        draw.rounded_rectangle([icx - 64, icy - 42, icx + 64, icy + 48], radius=22, fill="#ffffff")
        draw.line([(icx - 38, icy - 42), (icx - 58, icy - 68)], fill="#ffffff", width=7)
        draw.line([(icx + 38, icy - 42), (icx + 58, icy - 68)], fill="#ffffff", width=7)
        draw.ellipse([icx - 38, icy - 16, icx - 22, icy + 6], fill="#23ade5")
        draw.ellipse([icx + 22, icy - 16, icx + 38, icy + 6], fill="#23ade5")

    elif slug == "iqiyi-vip":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#00c455")
        draw.ellipse([icx - 54, icy - 54, icx + 54, icy + 54], outline="#ffffff", width=15)
        draw.polygon([(icx - 15, icy - 26), (icx + 26, icy), (icx - 15, icy + 26)], fill="#ffffff")

    elif slug == "meitu-vip":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#ff2a85")
        draw.ellipse([icx - 50, icy - 50, icx + 50, icy + 50], outline="#ffffff", width=14)
        draw.ellipse([icx - 20, icy - 20, icx + 20, icy + 20], fill="#ffffff")

    elif slug == "wink-vip":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#1e092b", outline="#a855f7", width=3)
        draw.polygon([(icx, icy - 55), (icx + 15, icy - 15), (icx + 55, icy), (icx + 15, icy + 15), (icx, icy + 55), (icx - 15, icy + 15), (icx - 55, icy), (icx - 15, icy - 15)], fill="#a855f7")
        draw.text((icx - 30, icy + 60), "WINK", fill="#ffffff")

    elif slug == "picsart-pro":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#14141c", outline="#d946ef", width=3)
        draw.ellipse([icx - 55, icy - 55, icx + 55, icy + 55], outline="#d946ef", width=14)
        draw.text((icx - 18, icy - 32), "P", fill="#ffffff")

    elif slug == "office-365-onedrive":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#eb3c00")
        draw.rounded_rectangle([icx - 58, icy - 58, icx - 6, icy - 6], radius=9, fill="#f25022")
        draw.rounded_rectangle([icx + 6, icy - 58, icx + 58, icy - 6], radius=9, fill="#7fba00")
        draw.rounded_rectangle([icx - 58, icy + 6, icx - 6, icy + 58], radius=9, fill="#00a4ef")
        draw.rounded_rectangle([icx + 6, icy + 6, icx + 58, icy + 58], radius=9, fill="#ffb900")

    elif slug == "scribd-premium":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#1e7b85")
        draw.rounded_rectangle([icx - 45, icy - 50, icx + 45, icy + 50], radius=10, fill="#ffffff")
        draw.line([(icx, icy - 50), (icx, icy + 50)], fill="#1e7b85", width=5)

    elif slug == "camscanner-vip":
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill="#1ba195")
        draw.line([(icx - 55, icy - 38), (icx - 55, icy - 60), (icx - 32, icy - 60)], fill="#ffffff", width=8)
        draw.line([(icx + 55, icy - 38), (icx + 55, icy - 60), (icx + 32, icy - 60)], fill="#ffffff", width=8)
        draw.line([(icx - 55, icy + 38), (icx - 55, icy + 60), (icx - 32, icy + 60)], fill="#ffffff", width=8)
        draw.line([(icx + 55, icy + 38), (icx + 55, icy + 60), (icx + 32, icy + 60)], fill="#ffffff", width=8)
        draw.text((icx - 35, icy - 22), "CS", fill="#ffffff")

    else:
        draw.rounded_rectangle([ix0, iy0, ix1, iy1], radius=48, fill=accent)
        draw.ellipse([icx - 52, icy - 52, icx + 52, icy + 52], outline="#ffffff", width=8)
        initial = title[:1] if title else "P"
        draw.text((icx - 18, icy - 30), initial, fill="#ffffff")

    # Bottom Titles
    draw.text((card_x0 + 50, card_y1 - 130), title, fill="#ffffff")
    draw.text((card_x0 + 50, card_y1 - 70), "⚡ 100% Legal & Bergaransi Resmi • Proses Cepat 24 Jam", fill="#30d158")

    main_filename = f"prod_{product_id}_{img_uuid}.jpg"
    thumb_filename = f"thumb_{product_id}_{img_uuid}.jpg"

    main_path = UPLOAD_DIR / main_filename
    thumb_path = UPLOAD_DIR / thumb_filename

    img.save(main_path, format="JPEG", quality=90)

    thumb_img = img.resize((400, 300), Image.Resampling.LANCZOS)
    thumb_img.save(thumb_path, format="JPEG", quality=88)

    return {
        "image_url": f"/static/uploads/{main_filename}",
        "thumbnail_url": f"/static/uploads/{thumb_filename}",
        "file_size": os.path.getsize(main_path)
    }

def seed_all():
    print("🚀 Menginisialisasi basis data PRIME APPS...")
    init_db()

    with get_db() as conn:
        print("🌱 Seeding Akun Pengguna...")
        admin_hash = hash_password("SuperAdmin2026!")
        conn.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, full_name, phone, role, status)
            VALUES (1, 'admin@primeapps.id', ?, 'Chief Administrator', '+62 812-3456-7890', 'superadmin', 'active')
        """, (admin_hash,))

        cust_hash = hash_password("Customer2026!")
        conn.execute("""
            INSERT OR REPLACE INTO users (id, email, password_hash, full_name, phone, role, status)
            VALUES (2, 'budi@gmail.com', ?, 'Budi Pratama', '081298765432', 'customer', 'active')
        """, (cust_hash,))

        print("🌱 Seeding Pengaturan Toko & Brand Identity...")
        settings = {
            "store_name": "PRIME APPS",
            "store_tagline": "Price List Resmi — Streaming, Design & AI Productivity",
            "store_description": "Upgrade your digital life! Toko resmi akun premium, invite, redeem, dan lisensi original terpercaya di Indonesia. 100% legal, aman, bergaransi penuh dengan proses kilat.",
            "hero_badge": "Official Price List 2026",
            "hero_title": "Upgrade Your Digital Life!",
            "hero_subtitle": "Dapatkan akun premium, invite, dan redeem resmi untuk Streaming, Design & Editing, serta AI & Productivity dengan harga paling bersahabat, 100% aman, dan garansi penuh.",
            "contact_email": "support@primeapps.id",
            "contact_whatsapp": "+62 812-3456-7890",
            "bank_name": "Bank Central Asia (BCA)",
            "bank_account_number": "8291-0029-381",
            "bank_account_holder": "PRIME APPS INDONESIA",
            "maintenance_mode": "0",
            "wa_order_enabled": "1"
        }
        for k, v in settings.items():
            conn.execute("""
                INSERT INTO store_settings (key, value, group_name, updated_at)
                VALUES (?, ?, 'general', CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """, (k, v))

        print("🌱 Seeding Kategori Resmi...")
        categories_data = [
            ("Streaming & Movies", "streaming-movies", "Akun premium film, series, anime, dan siaran langsung", "🎬", 1),
            ("Design & Editing", "design-editing", "Tools desain grafis, editing video, preset, dan motion graphics", "🎨", 2),
            ("AI & Productivity", "ai-productivity", "Asisten kecerdasan buatan, cloud storage, meeting, dan software produktivitas", "⚡", 3)
        ]
        for name, slug, desc, icon, order in categories_data:
            conn.execute("""
                INSERT INTO categories (name, slug, description, icon, display_order, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
                ON CONFLICT(slug) DO UPDATE SET name = excluded.name, icon = excluded.icon, description = excluded.description
            """, (name, slug, desc, icon, order))

        print("🌱 Seeding Brand Penerbit...")
        brands_data = [
            ("Netflix", "netflix", "https://netflix.com"),
            ("HBO Max", "hbo-max", "https://hbomax.com"),
            ("Disney+", "disney-plus", "https://disneyplus.com"),
            ("Viu", "viu", "https://viu.com"),
            ("Vidio", "vidio", "https://vidio.com"),
            ("WeTV", "wetv", "https://wetv.vip"),
            ("Amazon", "amazon", "https://primevideo.com"),
            ("Bstation", "bstation", "https://bilibili.tv"),
            ("iQIYI", "iqiyi", "https://iq.com"),
            ("LokLok", "loklok", "https://loklok.com"),
            ("Canva", "canva", "https://canva.com"),
            ("CapCut", "capcut", "https://capcut.com"),
            ("Alight Creative", "alight-motion", "https://alightmotion.com"),
            ("Meitu", "meitu", "https://meitu.com"),
            ("Picsart", "picsart", "https://picsart.com"),
            ("OpenAI", "openai", "https://openai.com"),
            ("Google", "google", "https://google.com"),
            ("Zoom", "zoom", "https://zoom.us"),
            ("Microsoft", "microsoft", "https://microsoft.com"),
            ("Scribd", "scribd", "https://scribd.com"),
            ("Duolingo", "duolingo", "https://duolingo.com"),
            ("CamScanner", "camscanner", "https://camscanner.com")
        ]
        for name, slug, web in brands_data:
            conn.execute("""
                INSERT INTO brands (name, slug, website, is_active)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(slug) DO UPDATE SET name = excluded.name, website = excluded.website
            """, (name, slug, web))

        print("🌱 Seeding 23 Produk Resmi Beserta Varian Harga...")
        products_data = [
            # =========================================================================
            # STREAMING & MOVIES
            # =========================================================================
            {
                "id": 1,
                "name": "Netflix Premium",
                "slug": "netflix-premium",
                "category_slug": "streaming-movies",
                "brand_slug": "netflix",
                "sku": "STR-NFLX",
                "short_description": "Nonton film dan series kualitas 4K UHD Ultra HD tanpa iklan.",
                "description": "Akun Netflix Premium resmi mendukung kualitas Ultra HD 4K, audio spatial, unduh offline, dan bebas tayangan ribuan film/series global. Tersedia garansi masa aktif.",
                "features": ["Kualitas Video Ultra HD 4K", "Bebas Iklan", "Mendukung Semua Perangkat (TV, HP, Laptop)", "100% Legal & Bergaransi", "Proses Cepat"],
                "regular_price": 35000,
                "sale_price": 30000,
                "is_featured": 1,
                "is_trending": 1,
                "delivery_type": "license_key",
                "color": "#e50914",
                "variants": [
                    {"name": "Netflix 1 Bulan", "regular_price": 35000, "sale_price": 30000, "sku": "NFLX-1M"}
                ]
            },
            {
                "id": 2,
                "name": "HBO Max",
                "slug": "hbo-max",
                "category_slug": "streaming-movies",
                "brand_slug": "hbo-max",
                "sku": "STR-HBOMAX",
                "short_description": "Akses konten blockbuster Warner Bros, HBO Original, DC, dan Harry Potter.",
                "description": "Nikmati film bioskop terbaik dan serial eksklusif HBO seperti House of the Dragon, The Last of Us, dan koleksi lengkap DC Universe.",
                "features": ["Akses Penuh Seluruh Film HBO", "Kualitas HD / 4K", "Subtitle Indonesia Resmi", "Garansi Penuh", "Pengiriman Instan"],
                "regular_price": 12000,
                "sale_price": 8000,
                "is_featured": 0,
                "is_trending": 1,
                "delivery_type": "license_key",
                "color": "#5822b4",
                "variants": [
                    {"name": "HBO Max 1 Bulan", "regular_price": 12000, "sale_price": 8000, "sku": "HBO-1M"}
                ]
            },
            {
                "id": 3,
                "name": "Disney+ Hotstar",
                "slug": "disney-plus-hotstar",
                "category_slug": "streaming-movies",
                "brand_slug": "disney-plus",
                "sku": "STR-DISNEY",
                "short_description": "Koleksi Disney, Marvel, Pixar, Star Wars, dan film lokal bioskop Indonesia.",
                "description": "Streaming Disney+ Hotstar resmi untuk hiburan keluarga tanpa batas. Tonton Marvel Studios, anime populer, dan rilisan film Indonesia terhangat.",
                "features": ["Marvel Studios & Star Wars Lengkap", "Bebas Iklan", "Dubbing & Subtitle Indonesia", "Akses Semua Perangkat", "Garansi Aktif 1 Bulan"],
                "regular_price": 15000,
                "sale_price": 12000,
                "is_featured": 1,
                "is_trending": 0,
                "delivery_type": "license_key",
                "color": "#0063e5",
                "variants": [
                    {"name": "Disney+ Premium 1 Bulan", "regular_price": 15000, "sale_price": 12000, "sku": "DIS-1M"}
                ]
            },
            {
                "id": 4,
                "name": "Viu Premium",
                "slug": "viu-premium",
                "category_slug": "streaming-movies",
                "brand_slug": "viu",
                "sku": "STR-VIU",
                "short_description": "Pusat drama Korea, anime, dan serial Asia terbaru tercepat.",
                "description": "Nonton drakor on-going dan anime terlengkap dengan subtitle Indonesia super cepat hanya 8 jam setelah tayang di Korea.",
                "features": ["Drama Korea On-Going", "Download Tayangan Tanpa Batas", "Kualitas Full HD", "Bebas Iklan", "100% Legal & Bergaransi"],
                "regular_price": 5000,
                "sale_price": 3000,
                "is_featured": 0,
                "is_trending": 1,
                "delivery_type": "license_key",
                "color": "#f8b800",
                "variants": [
                    {"name": "Viu Premium 1 Bulan", "regular_price": 5000, "sale_price": 3000, "sku": "VIU-1M"}
                ]
            },
            {
                "id": 5,
                "name": "Vidio Platinum",
                "slug": "vidio-platinum",
                "category_slug": "streaming-movies",
                "brand_slug": "vidio",
                "sku": "STR-VIDIO",
                "short_description": "Streaming Liga 1, BRI Liga, Vidio Original Series, dan tayangan olahraga favorit.",
                "description": "Akses platinum resmi untuk tayangan live match sepak bola, Vidio Original Series terpopuler, film Hollywood, dan channel TV nasional jernih.",
                "features": ["Live Streaming Sepak Bola & Sports", "Vidio Original Series Eksklusif", "Bebas Iklan", "Kualitas HD Jernih", "Garansi Aktif"],
                "regular_price": 28000,
                "sale_price": 23000,
                "is_featured": 1,
                "is_trending": 1,
                "delivery_type": "license_key",
                "color": "#ed1c24",
                "variants": [
                    {"name": "Vidio Platinum 1 Bulan", "regular_price": 28000, "sale_price": 23000, "sku": "VID-1M"}
                ]
            },
            {
                "id": 6,
                "name": "WeTV VIP",
                "slug": "wetv-vip",
                "category_slug": "streaming-movies",
                "brand_slug": "wetv",
                "sku": "STR-WETV",
                "short_description": "Serial drama Asia, drachin romantis, anime, dan WeTV Original.",
                "description": "Nikmati episode terbaru lebih awal dengan lencana VIP eksklusif. Tonton drama China dan WeTV Original favorit tanpa jeda iklan.",
                "features": ["Nonton Episode Lebih Awal", "Kualitas Gambar 1080P", "Subtitle Multi-Bahasa", "Audio Dolby", "Garansi Penuh 1 Bulan"],
                "regular_price": 10000,
                "sale_price": 8000,
                "is_featured": 0,
                "is_trending": 0,
                "delivery_type": "license_key",
                "color": "#00c354",
                "variants": [
                    {"name": "WeTV VIP 1 Bulan", "regular_price": 10000, "sale_price": 8000, "sku": "WETV-1M"}
                ]
            },
            {
                "id": 7,
                "name": "Amazon Prime Video",
                "slug": "amazon-prime-video",
                "category_slug": "streaming-movies",
                "brand_slug": "amazon",
                "sku": "STR-PRIMEVID",
                "short_description": "Film original Hollywood, The Boys, Rings of Power, dan blockbuster bioskop.",
                "description": "Akses hiburan global berkualitas tinggi dari Amazon Studios dengan audio jernih dan fitur X-Ray pengenal aktor/musik.",
                "features": ["Amazon Originals Terbaik", "Fitur X-Ray Spesial", "Kualitas 4K HDR", "Unduh Nonton Offline", "Proses Cepat"],
                "regular_price": 8000,
                "sale_price": 5500,
                "is_featured": 0,
                "is_trending": 0,
                "delivery_type": "license_key",
                "color": "#00a8e1",
                "variants": [
                    {"name": "Prime Video 1 Bulan", "regular_price": 8000, "sale_price": 5500, "sku": "PVID-1M"}
                ]
            },
            {
                "id": 8,
                "name": "Bstation VIP",
                "slug": "bstation-vip",
                "category_slug": "streaming-movies",
                "brand_slug": "bstation",
                "sku": "STR-BSTATION",
                "short_description": "Komunitas dan streaming anime terbesar dengan update simulcast harian.",
                "description": "Nonton anime musim baru tayang bersamaan dengan Jepang. Kualitas 1080P/4K khusus member VIP dengan audio surround.",
                "features": ["Simulcast Anime Musim Baru", "Kualitas 1080P / 4K", "Bebas Iklan", "Koleksi Anime Terlengkap", "Garansi 1 Bulan"],
                "regular_price": 8000,
                "sale_price": 5000,
                "is_featured": 0,
                "is_trending": 1,
                "delivery_type": "license_key",
                "color": "#00a1d6",
                "variants": [
                    {"name": "Bstation VIP 1 Bulan", "regular_price": 8000, "sale_price": 5000, "sku": "BSTA-1M"}
                ]
            },
            {
                "id": 9,
                "name": "iQIYI VIP",
                "slug": "iqiyi-vip",
                "category_slug": "streaming-movies",
                "brand_slug": "iqiyi",
                "sku": "STR-IQIYI",
                "short_description": "Koleksi drama Mandarin, anime, dan variety show Asia terbaik.",
                "description": "Nikmati drama Asia beresolusi tinggi dengan audio Dolby Atmos. Bebas tonton seluruh episode VIP tanpa gangguan.",
                "features": ["Akses Eksklusif Drama VIP", "Audio Dolby Atmos & 1080P", "Subtitle Multi-Bahasa", "Garansi Resmi", "Aktivasi Cepat"],
                "regular_price": 12000,
                "sale_price": 8000,
                "is_featured": 0,
                "is_trending": 0,
                "delivery_type": "license_key",
                "color": "#00b259",
                "variants": [
                    {"name": "iQIYI VIP 1 Bulan", "regular_price": 12000, "sale_price": 8000, "sku": "IQ-1M"}
                ]
            },
            {
                "id": 10,
                "name": "LokLok VIP",
                "slug": "loklok-vip",
                "category_slug": "streaming-movies",
                "brand_slug": "loklok",
                "sku": "STR-LOKLOK",
                "short_description": "Nonton ribuan film barat, drama Asia, dan anime dalam satu aplikasi ringan.",
                "description": "Aplikasi streaming serbaguna dengan kualitas jernih dan server cepat tanpa hambatan buffering.",
                "features": ["Semua Kategori Film & Drama", "Bebas Iklan Mengganggu", "Server Kecepatan Tinggi", "Garansi Aktif", "Proses Cepat"],
                "regular_price": 12000,
                "sale_price": 9000,
                "is_featured": 0,
                "is_trending": 0,
                "delivery_type": "license_key",
                "color": "#3366ff",
                "variants": [
                    {"name": "LokLok VIP 1 Bulan", "regular_price": 12000, "sale_price": 9000, "sku": "LOK-1M"}
                ]
            },

            # =========================================================================
            # DESIGN & EDITING
            # =========================================================================
            {
                "id": 11,
                "name": "Canva Pro",
                "slug": "canva-pro",
                "category_slug": "design-editing",
                "brand_slug": "canva",
                "sku": "DSN-CANVA",
                "short_description": "Akses 100+ juta foto/video stok premium, Brand Kit, dan Magic Studio AI.",
                "description": "Alat desain grafis nomor satu di dunia. Akses seluruh template premium, penghapus latar belakang instan (Background Remover), dan font eksklusif.",
                "features": ["100+ Juta Foto & Elemen Pro", "Penghapus Background 1 Klik", "Magic Resize & Magic Eraser AI", "Bisa Desain di HP & Laptop", "Garansi Penuh Sesuai Paket"],
                "regular_price": 5000,
                "sale_price": 3000,
                "is_featured": 1,
                "is_trending": 1,
                "delivery_type": "account_invite",
                "color": "#00c4cc",
                "variants": [
                    {"name": "Canva Pro Member 1 Bulan", "regular_price": 5000, "sale_price": 3000, "sku": "CNV-MEM-1M"},
                    {"name": "Canva Pro Head/Owner 1 Bulan", "regular_price": 8000, "sale_price": 5000, "sku": "CNV-OWN-1M"},
                    {"name": "Canva Pro Member Lifetime", "regular_price": 10000, "sale_price": 5000, "sku": "CNV-MEM-LT"}
                ]
            },
            {
                "id": 12,
                "name": "CapCut Pro",
                "slug": "capcut-pro",
                "category_slug": "design-editing",
                "brand_slug": "capcut",
                "sku": "DSN-CAPCUT",
                "short_description": "Editing video profesional dengan efek pro, auto caption, dan penghapus flicker.",
                "description": "Software editing video paling populer untuk konten kreator TikTok, Instagram Reels, dan YouTube Shorts. Buka semua fitur pro, transisi dan filter berbayar.",
                "features": ["Fitur Pro & Efek Eksklusif Terbuka", "Auto Subtitle / Caption Otomatis", "Cloud Storage Tambahan", "Bebas Watermark & Export 4K", "Tersedia Opsi Private & Member"],
                "regular_price": 8000,
                "sale_price": 6000,
                "is_featured": 1,
                "is_trending": 1,
                "delivery_type": "license_key",
                "color": "#000000",
                "variants": [
                    {"name": "CapCut Pro Private 7 Hari", "regular_price": 8000, "sale_price": 6000, "sku": "CPCT-PRV-7D"},
                    {"name": "CapCut Pro Member 30 Hari", "regular_price": 25000, "sale_price": 20000, "sku": "CPCT-MEM-30D"},
                    {"name": "CapCut Pro Private 42 Hari", "regular_price": 30000, "sale_price": 23000, "sku": "CPCT-PRV-42D"}
                ]
            },
            {
                "id": 13,
                "name": "Alight Motion",
                "slug": "alight-motion",
                "category_slug": "design-editing",
                "brand_slug": "alight-motion",
                "sku": "DSN-ALIGHT",
                "short_description": "Aplikasi motion graphics, visual effects, dan video compositing di smartphone.",
                "description": "Buka seluruh efek visual lanjutan, animasi keyframe presisi, dan dukungan impor preset XML tanpa watermark.",
                "features": ["Bebas Watermark Alight Motion", "Akses Semua Efek & Shaders Pro", "Impor Preset XML & Font Kustom", "Render 1080P 60FPS", "Garansi Private"],
                "regular_price": 3000,
                "sale_price": 2400,
                "is_featured": 0,
                "is_trending": 1,
                "delivery_type": "license_key",
                "color": "#00c49f",
                "variants": [
                    {"name": "Alight Motion Private 6 Bulan", "regular_price": 3500, "sale_price": 2400, "sku": "AM-PRV-6M"},
                    {"name": "Alight Motion Private 1 Tahun", "regular_price": 4000, "sale_price": 2800, "sku": "AM-PRV-1Y"}
                ]
            },
            {
                "id": 14,
                "name": "Meitu VIP",
                "slug": "meitu-vip",
                "category_slug": "design-editing",
                "brand_slug": "meitu",
                "sku": "DSN-MEITU",
                "short_description": "Editor foto & video portrait terbaik dengan fitur AI Retouch dan filter estetis.",
                "description": "Sempurnakan foto potret dan video dengan AI Face Slimming, Skin Smoothing, dan ratusan filter estetik kelas studio profesional.",
                "features": ["AI Body & Face Retouch Pro", "Filter Premium Tanpa Watermark", "Peningkatan Kualitas HD Otomatis", "Garansi Aktif Penuh", "Proses Cepat"],
                "regular_price": 5000,
                "sale_price": 4200,
                "is_featured": 0,
                "is_trending": 0,
                "delivery_type": "license_key",
                "color": "#ff3366",
                "variants": [
                    {"name": "Meitu VIP+ 7 Hari", "regular_price": 5500, "sale_price": 4200, "sku": "MT-7D"},
                    {"name": "Meitu VIP+ 14 Hari", "regular_price": 8000, "sale_price": 6000, "sku": "MT-14D"}
                ]
            },
            {
                "id": 15,
                "name": "Wink VIP",
                "slug": "wink-vip",
                "category_slug": "design-editing",
                "brand_slug": "meitu",
                "sku": "DSN-WINK",
                "short_description": "Video beauty retouching, AI makeup, dan perbaikan kualitas video buram ke 4K.",
                "description": "Aplikasi khusus peningkatan kualitas video portrait. Hasilkan video jernih berkualitas sinematik dengan AI enhancer.",
                "features": ["AI Video Quality Repair", "Face & Body Reshaping", "Preset Warna Aesthetic", "Garansi Sesuai Durasi", "Aktivasi Instan"],
                "regular_price": 5000,
                "sale_price": 4000,
                "is_featured": 0,
                "is_trending": 0,
                "delivery_type": "license_key",
                "color": "#8a2be2",
                "variants": [
                    {"name": "Wink VIP+ 7 Hari", "regular_price": 5000, "sale_price": 4000, "sku": "WNK-7D"},
                    {"name": "Wink VIP+ 14 Hari", "regular_price": 7000, "sale_price": 5000, "sku": "WNK-14D"}
                ]
            },
            {
                "id": 16,
                "name": "Picsart Pro",
                "slug": "picsart-pro",
                "category_slug": "design-editing",
                "brand_slug": "picsart",
                "sku": "DSN-PICSART",
                "short_description": "Suite kreasi konten all-in-one: cutout AI, stiker premium, dan editing kolase.",
                "description": "Buka seluruh library jutaan stiker, font eksklusif, background remover, dan generator AI canggih di Picsart Gold.",
                "features": ["Bebas Iklan", "Ribuan Template & Font Gold", "AI Image Generator & Cutout", "Akun Private Terpercaya", "Garansi Penuh"],
                "regular_price": 10000,
                "sale_price": 7000,
                "is_featured": 0,
                "is_trending": 0,
                "delivery_type": "license_key",
                "color": "#0070ba",
                "variants": [
                    {"name": "Picsart Pro Private 7 Hari", "regular_price": 10000, "sale_price": 7000, "sku": "PCS-7D"}
                ]
            },

            # =========================================================================
            # AI & PRODUCTIVITY
            # =========================================================================
            {
                "id": 17,
                "name": "OpenAI ChatGPT Plus & Go",
                "slug": "chatgpt-plus-go",
                "category_slug": "ai-productivity",
                "brand_slug": "openai",
                "sku": "PRD-CGPT",
                "short_description": "Asisten AI terdepan dengan model GPT-4o, analisis data, Canvas, dan Voice Mode.",
                "description": "Dapatkan akses prioritas ke kecerdasan buatan terhebat dunia. Tersedia opsi ChatGPT Go hemat maupun ChatGPT Plus Private bergaransi penuh.",
                "features": ["Model GPT-4o & Canvas Code Editor", "Advanced Voice Mode Cepat", "DALL-E 3 Image Generation", "Garansi Penuh Masa Aktif", "100% Legal & Aman"],
                "regular_price": 10000,
                "sale_price": 7000,
                "is_featured": 1,
                "is_trending": 1,
                "delivery_type": "license_key",
                "color": "#10a37f",
                "variants": [
                    {"name": "ChatGPT Go 3 Bulan (Link)", "regular_price": 10000, "sale_price": 7000, "sku": "CGPT-GO-3M"},
                    {"name": "ChatGPT Plus 1 Bulan (Private)", "regular_price": 15000, "sale_price": 10000, "sku": "CGPT-PLS-1M"}
                ]
            },
            {
                "id": 18,
                "name": "Google Gemini AI",
                "slug": "google-gemini-ai",
                "category_slug": "ai-productivity",
                "brand_slug": "google",
                "sku": "PRD-GEMINI",
                "short_description": "Model AI tercanggih Google dengan integrasi Workspace dan konteks jendela 1M token.",
                "description": "Aktivasi resmi akun Google Gemini Advanced. Terhubung mulus dengan Gmail, Google Docs, Drive, dan analisis kode rumit.",
                "features": ["Model Gemini 1.5 Pro Terbaru", "Jendela Konteks 1 Juta Token", "Integrasi Google Docs & Gmail", "Garansi Masa Aktif Penuh", "Aktivasi Redeem Resmi"],
                "regular_price": 15000,
                "sale_price": 11000,
                "is_featured": 1,
                "is_trending": 1,
                "delivery_type": "license_key",
                "color": "#4285f4",
                "variants": [
                    {"name": "Gemini AI Redeem 3 Bulan", "regular_price": 15000, "sale_price": 11000, "sku": "GEM-3M"},
                    {"name": "Gemini AI Redeem 18 Bulan", "regular_price": 35000, "sale_price": 27000, "sku": "GEM-18M"}
                ]
            },
            {
                "id": 19,
                "name": "Zoom Meeting Pro",
                "slug": "zoom-meeting-pro",
                "category_slug": "ai-productivity",
                "brand_slug": "zoom",
                "sku": "PRD-ZOOM",
                "short_description": "Meeting online tanpa batas 40 menit, kapasitas 100+ peserta, dan cloud recording.",
                "description": "Solusi rapat online tanpa khawatir terputus batas waktu 40 menit. Dilengkapi fitur live streaming ke YouTube/Facebook dan co-host.",
                "features": ["Durasi Rapat Tanpa Batas 40 Menit", "Kapasitas Hingga 100 Peserta", "Fitur Co-Host & Polling", "Cloud & Local Recording", "Akun Private Bergaransi"],
                "regular_price": 5000,
                "sale_price": 3500,
                "is_featured": 0,
                "is_trending": 1,
                "delivery_type": "license_key",
                "color": "#2d8cff",
                "variants": [
                    {"name": "Zoom Pro Private 7 Hari", "regular_price": 5000, "sale_price": 3500, "sku": "ZM-7D"},
                    {"name": "Zoom Pro Private 14 Hari", "regular_price": 6000, "sale_price": 4000, "sku": "ZM-14D"},
                    {"name": "Zoom Pro Private 30 Hari", "regular_price": 10000, "sale_price": 8000, "sku": "ZM-30D"}
                ]
            },
            {
                "id": 20,
                "name": "Office 365 + 1TB OneDrive",
                "slug": "office-365-onedrive",
                "category_slug": "ai-productivity",
                "brand_slug": "microsoft",
                "sku": "PRD-OFFICE",
                "short_description": "Word, Excel, PowerPoint, Outlook, dan 1.000 GB OneDrive Cloud Storage.",
                "description": "Suite aplikasi kerja terlengkap Microsoft. Gunakan aplikasi desktop resmi di 5 perangkat sekaligus (Windows, Mac, Android, iOS).",
                "features": ["Word, Excel, PowerPoint Lengkap", "1TB (1.000 GB) Penyimpanan OneDrive", "Bisa Pasang di 5 Perangkat", "Akun Private Resmi", "Garansi Penuh 1 Bulan"],
                "regular_price": 15000,
                "sale_price": 9000,
                "is_featured": 1,
                "is_trending": 0,
                "delivery_type": "license_key",
                "color": "#d83b01",
                "variants": [
                    {"name": "Office 365 1 Bulan (Private)", "regular_price": 15000, "sale_price": 9000, "sku": "O365-1M"}
                ]
            },
            {
                "id": 21,
                "name": "Scribd Premium",
                "slug": "scribd-premium",
                "category_slug": "ai-productivity",
                "brand_slug": "scribd",
                "sku": "PRD-SCRIBD",
                "short_description": "Perpustakaan digital jutaan ebook, audiobook, dokumen riset, dan jurnal ilmiah.",
                "description": "Download dan baca buku bestseller dunia, dokumen tugas kuliah, dan audiobook tanpa batas langsung dari aplikasi Scribd.",
                "features": ["Jutaan Ebook & Audiobook", "Download Dokumen Riset Tanpa Batas", "Bebas Iklan", "100% Legal & Bergaransi", "Pengiriman Cepat"],
                "regular_price": 9000,
                "sale_price": 6000,
                "is_featured": 0,
                "is_trending": 0,
                "delivery_type": "license_key",
                "color": "#1e7b85",
                "variants": [
                    {"name": "Scribd Premium 1 Bulan", "regular_price": 9000, "sale_price": 6000, "sku": "SCB-1M"}
                ]
            },
            {
                "id": 22,
                "name": "Duolingo Super",
                "slug": "duolingo-super",
                "category_slug": "ai-productivity",
                "brand_slug": "duolingo",
                "sku": "PRD-DUO",
                "short_description": "Belajar bahasa asing seru tanpa batas hati (Unlimited Hearts) dan tanpa jeda iklan.",
                "description": "Kuasai bahasa Inggris, Jepang, Mandarin, dan puluhan bahasa dunia lebih cepat dengan Duolingo Super resmi.",
                "features": ["Nyawa Tak Terbatas (Unlimited Hearts)", "Bebas Iklan Pengganggu", "Latihan Khusus Kesalahan (Mistakes Review)", "Garansi 1 Bulan", "Aktivasi Instan"],
                "regular_price": 10000,
                "sale_price": 6500,
                "is_featured": 0,
                "is_trending": 1,
                "delivery_type": "license_key",
                "color": "#58cc02",
                "variants": [
                    {"name": "Duolingo Super 1 Bulan", "regular_price": 10000, "sale_price": 6500, "sku": "DUO-1M"}
                ]
            },
            {
                "id": 23,
                "name": "CamScanner VIP",
                "slug": "camscanner-vip",
                "category_slug": "ai-productivity",
                "brand_slug": "camscanner",
                "sku": "PRD-CAMSCAN",
                "short_description": "Scan dokumen HD tanpa watermark, OCR ekstraksi teks ke Word/Excel, dan cloud 10GB.",
                "description": "Alat scan dokumen smartphone terbaik. Hasilkan scan PDF jernih tanpa tanda air, tanda tangan elektronik, dan konversi ke Word.",
                "features": ["Bebas Watermark CamScanner", "OCR Konversi Gambar ke Teks/Excel", "Kualitas Scan HD Resolusi Tinggi", "Garansi Penuh 1 Bulan", "Proses Cepat"],
                "regular_price": 9000,
                "sale_price": 6000,
                "is_featured": 0,
                "is_trending": 0,
                "delivery_type": "license_key",
                "color": "#1ba195",
                "variants": [
                    {"name": "CamScanner VIP 1 Bulan", "regular_price": 9000, "sale_price": 6000, "sku": "CS-1M"}
                ]
            }
        ]

        # Clear existing products to ensure clean exact catalog
        conn.execute("DELETE FROM products")
        conn.execute("DELETE FROM product_variants")
        conn.execute("DELETE FROM product_images")
        conn.execute("DELETE FROM license_keys")

        for prod in products_data:
            p_id = prod["id"]
            cat_row = conn.execute("SELECT id FROM categories WHERE slug = ?", (prod["category_slug"],)).fetchone()
            brand_row = conn.execute("SELECT id FROM brands WHERE slug = ?", (prod["brand_slug"],)).fetchone()

            conn.execute("""
                INSERT INTO products (
                    id, name, slug, category_id, brand_id, sku, short_description, description,
                    features_json, regular_price, sale_price, is_featured, is_trending,
                    status, delivery_type, sort_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
            """, (
                p_id, prod["name"], prod["slug"], cat_row["id"] if cat_row else None,
                brand_row["id"] if brand_row else None, prod["sku"], prod["short_description"],
                prod["description"], json.dumps(prod["features"]), prod["regular_price"],
                prod["sale_price"], prod["is_featured"], prod["is_trending"], prod["delivery_type"], p_id
            ))

            # Insert all product variants
            for v_idx, v in enumerate(prod.get("variants", [])):
                conn.execute("""
                    INSERT INTO product_variants (product_id, name, regular_price, sale_price, sku, sort_order, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (p_id, v["name"], v["regular_price"], v["sale_price"], v["sku"], v_idx))

            # Generate real images on disk
            img_info = generate_product_image(p_id, prod["name"], prod["short_description"][:45] + "...", prod["color"], slug=prod["slug"])
            
            conn.execute("""
                INSERT INTO product_images (product_id, image_url, thumbnail_url, alt_text, is_primary, display_order, file_size)
                VALUES (?, ?, ?, ?, 1, 0, ?)
            """, (p_id, img_info["image_url"], img_info["thumbnail_url"], prod["name"], img_info["file_size"]))

            # Generate initial license keys in pool (5 keys per product)
            for k_i in range(1, 6):
                sku_tag = prod["sku"].replace("-", "")
                key_code = f"PRIME-{sku_tag}-{uuid.uuid4().hex[:6].upper()}-{k_i:02d}"
                conn.execute("""
                    INSERT INTO license_keys (product_id, license_code, is_used)
                    VALUES (?, ?, 0)
                """, (p_id, key_code))

        print("🌱 Seeding Voucher Promosi...")
        vouchers_data = [
            ("DISKON10", "percentage", 10, 10000, 5000, 100, 4),
            ("HEMAT5RB", "fixed", 5000, 20000, 0, 50, 2),
            ("PRIMEPROMO", "percentage", 15, 25000, 10000, 50, 0)
        ]
        conn.execute("DELETE FROM vouchers")
        for code, dtype, dval, min_ord, max_disc, limit, used in vouchers_data:
            conn.execute("""
                INSERT INTO vouchers (code, discount_type, discount_value, min_order_amount, max_discount, usage_limit, times_used, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (code, dtype, dval, min_ord, max_disc, limit, used))

        print("🌱 Seeding Sample Completed Orders untuk Grafik Analytics...")
        conn.execute("DELETE FROM orders")
        conn.execute("DELETE FROM order_items")
        conn.execute("DELETE FROM payments")

        sample_orders = [
            ("PRM-20261026-A101", 2, "Budi Pratama", "budi@gmail.com", "081298765432", 30000, 0, 30000, "QRIS", "PAID", "2026-10-26 14:20:00", 1, "Netflix Premium (Netflix 1 Bulan)", "PRIME-STRNFLX-882B-01"),
            ("PRM-20261027-B202", 2, "Budi Pratama", "budi@gmail.com", "081298765432", 20000, 2000, 18000, "BCA_VA", "PAID", "2026-10-27 10:15:00", 12, "CapCut Pro (CapCut Pro Member 30 Hari)", "PRIME-DSNCAP-991A-01"),
            ("PRM-20261028-C303", 2, "Budi Pratama", "budi@gmail.com", "081298765432", 10000, 0, 10000, "QRIS", "PAID", "2026-10-28 09:30:00", 17, "OpenAI ChatGPT Plus (ChatGPT Plus 1 Bulan)", "PRIME-PRDCGPT-773C-01")
        ]

        for ord_num, u_id, c_name, c_email, c_phone, sub, disc, tot, meth, status, c_date, p_id, p_name, l_code in sample_orders:
            cur = conn.execute("""
                INSERT INTO orders (
                    order_number, user_id, customer_name, customer_email, customer_phone,
                    subtotal, discount_amount, total_amount, payment_method,
                    payment_status, fulfillment_status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'FULFILLED', ?)
            """, (ord_num, u_id, c_name, c_email, c_phone, sub, disc, tot, meth, status, c_date))
            o_id = cur.lastrowid
            conn.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, price, quantity, subtotal, digital_payload)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (o_id, p_id, p_name, sub, sub, l_code))
            conn.execute("""
                INSERT INTO payments (order_id, transaction_id, gateway, payment_type, amount, status, created_at)
                VALUES (?, ?, 'midtrans_simulation', ?, ?, 'SETTLEMENT', ?)
            """, (o_id, f"TX-{ord_num}", meth, tot, c_date))

    print("✨ Seeding seluruh 23 produk resmi & varian selesai 100%!")

if __name__ == "__main__":
    seed_all()
