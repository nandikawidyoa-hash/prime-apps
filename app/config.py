import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
STATIC_DIR = APP_DIR / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"

# Smart Database Path Detection:
# 1. Honors explicit DATABASE_FILE env var if provided.
# 2. In local sandbox with /working_dir 9p mount, uses /tmp/webstore.db.
# 3. In Android Termux or production VPS, uses BASE_DIR / "webstore.db" (local project directory).
db_env = os.getenv("DATABASE_FILE")
if db_env:
    DATABASE_PATH = Path(db_env)
elif os.path.exists("/working_dir/c_1122a5c15cf30180") and os.path.exists("/tmp") and os.access("/tmp", os.W_OK):
    DATABASE_PATH = Path("/tmp/webstore.db")
else:
    DATABASE_PATH = BASE_DIR / "webstore.db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.getenv("SECRET_KEY", "primeapps-super-secret-key-2026-production-grade")
SESSION_COOKIE_NAME = "prime_session"
ADMIN_SESSION_COOKIE_NAME = "prime_admin_session"

# Image upload limits
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}

# Payment Gateway Simulation
PAYMENT_SECRET = os.getenv("PAYMENT_SECRET", "pg_secret_midtrans_simulation_prime_2026")

# Default Brand Settings
DEFAULT_STORE_NAME = "PRIME APPS"
DEFAULT_STORE_TAGLINE = "Toko Digital Premium & Lisensi Aplikasi Resmi"
DEFAULT_CURRENCY = "IDR"
