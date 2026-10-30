import os
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import UploadFile, HTTPException
from PIL import Image

from app.config import (
    UPLOAD_DIR,
    MAX_UPLOAD_SIZE,
    ALLOWED_IMAGE_MIMES,
    ALLOWED_IMAGE_EXTENSIONS
)
from app.database import get_db

THUMBNAIL_SIZE = (400, 300)
MAIN_SIZE = (1280, 800)

async def validate_image_file(file: UploadFile) -> bytes:
    """Validates file mime type, extension, and size."""
    if file.content_type not in ALLOWED_IMAGE_MIMES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipe file tidak didukung: {file.content_type}. Gunakan JPG, PNG, atau WebP."
        )
    
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Ekstensi file tidak valid: {ext}. Gunakan .jpg, .png, atau .webp."
        )
    
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Ukuran file melebihi batas maksimum 5MB (Ukuran saat ini: {len(content) / (1024*1024):.2f}MB)."
        )
    
    # Reset file pointer for future reads if needed
    await file.seek(0)
    return content

def save_product_image(
    file_bytes: bytes,
    original_filename: str,
    product_id: int,
    alt_text: Optional[str] = None,
    is_primary: bool = False,
    display_order: int = 0
) -> dict:
    """Processes, resizes, optimizes, and stores a product image and its thumbnail."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    file_uuid = uuid.uuid4().hex
    
    import io
    img = Image.open(io.BytesIO(file_bytes))
    
    # Normalize color mode to RGB if RGBA/P
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
        target_format = "JPEG"
        file_ext = ".jpg"
    elif img.format in ("JPEG", "JPG"):
        target_format = "JPEG"
        file_ext = ".jpg"
    elif img.format == "WEBP":
        target_format = "WEBP"
        file_ext = ".webp"
    else:
        target_format = "JPEG"
        file_ext = ".jpg"
        
    main_filename = f"prod_{product_id}_{file_uuid}{file_ext}"
    thumb_filename = f"thumb_{product_id}_{file_uuid}{file_ext}"
    
    main_path = UPLOAD_DIR / main_filename
    thumb_path = UPLOAD_DIR / thumb_filename
    
    # Save main image
    img.save(main_path, format=target_format, quality=88, optimize=True)
    
    # Generate and save thumbnail
    thumb_img = img.copy()
    thumb_img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
    thumb_img.save(thumb_path, format=target_format, quality=85, optimize=True)
    
    file_size = os.path.getsize(main_path)
    image_url = f"/static/uploads/{main_filename}"
    thumb_url = f"/static/uploads/{thumb_filename}"
    
    with get_db() as conn:
        # If this is set as primary, unset other primaries for this product
        if is_primary:
            conn.execute("UPDATE product_images SET is_primary = 0 WHERE product_id = ?", (product_id,))
        else:
            # If no primary exists yet, make this primary
            existing = conn.execute("SELECT COUNT(*) as cnt FROM product_images WHERE product_id = ?", (product_id,)).fetchone()
            if existing["cnt"] == 0:
                is_primary = True

        cursor = conn.execute("""
            INSERT INTO product_images (product_id, image_url, thumbnail_url, alt_text, is_primary, display_order, file_size)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (product_id, image_url, thumb_url, alt_text or original_filename, 1 if is_primary else 0, display_order, file_size))
        image_id = cursor.lastrowid
        
    return {
        "id": image_id,
        "product_id": product_id,
        "image_url": image_url,
        "thumbnail_url": thumb_url,
        "alt_text": alt_text,
        "is_primary": bool(is_primary),
        "display_order": display_order,
        "file_size": file_size
    }

def delete_product_image(image_id: int, product_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute("SELECT image_url, thumbnail_url, is_primary FROM product_images WHERE id = ? AND product_id = ?", (image_id, product_id)).fetchone()
        if not row:
            return False
            
        # Delete files from disk safely
        for url in [row["image_url"], row["thumbnail_url"]]:
            if url:
                filename = url.replace("/static/uploads/", "").replace("/uploads/", "")
                file_path = UPLOAD_DIR / filename
                if file_path.exists():
                    try:
                        file_path.unlink()
                    except Exception:
                        pass
        
        conn.execute("DELETE FROM product_images WHERE id = ?", (image_id,))
        
        # If the deleted image was primary, set next available image as primary
        if row["is_primary"]:
            next_img = conn.execute("SELECT id FROM product_images WHERE product_id = ? ORDER BY display_order ASC, id ASC LIMIT 1", (product_id,)).fetchone()
            if next_img:
                conn.execute("UPDATE product_images SET is_primary = 1 WHERE id = ?", (next_img["id"],))
                
        return True

def get_fallback_banner(filename: str = "") -> bytes:
    """Generates a clean fallback branded banner in case an image is missing on disk."""
    import io
    from PIL import Image, ImageDraw
    width, height = 800, 500
    img = Image.new("RGB", (width, height), color="#121218")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([20, 20, width - 20, height - 20], radius=16, fill="#1c1c24", outline="#3b82f6", width=2)
    draw.rounded_rectangle([50, 45, 230, 85], radius=12, fill="#3b82f6")
    draw.text((65, 55), "PRIME APPS", fill="#ffffff")
    draw.text((50, 160), "PRODUK DIGITAL RESMI", fill="#ffffff")
    draw.text((50, 210), "⚡ 100% Legal & Bergaransi Penuh", fill="#30d158")
    draw.text((50, 260), "Aktivasi Cepat • Layanan 24 Jam", fill="#9ca3af")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()
