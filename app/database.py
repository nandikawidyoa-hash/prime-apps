import sqlite3
import json
from contextlib import contextmanager
from app.config import DATABASE_PATH

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 10000;")
    return conn

@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            role TEXT DEFAULT 'customer',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            icon TEXT,
            display_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            logo_url TEXT,
            website TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
            brand_id INTEGER REFERENCES brands(id) ON DELETE SET NULL,
            sku TEXT,
            short_description TEXT,
            description TEXT,
            features_json TEXT DEFAULT '[]',
            regular_price INTEGER NOT NULL,
            sale_price INTEGER,
            is_featured INTEGER DEFAULT 0,
            is_trending INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            delivery_type TEXT DEFAULT 'license_key',
            delivery_instructions TEXT,
            seo_title TEXT,
            seo_description TEXT,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS product_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            regular_price INTEGER NOT NULL,
            sale_price INTEGER,
            sku TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS product_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            image_url TEXT NOT NULL,
            thumbnail_url TEXT,
            alt_text TEXT,
            is_primary INTEGER DEFAULT 0,
            display_order INTEGER DEFAULT 0,
            file_size INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS license_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            variant_id INTEGER REFERENCES product_variants(id) ON DELETE SET NULL,
            license_code TEXT NOT NULL,
            is_used INTEGER DEFAULT 0,
            order_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS carts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            session_id TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cart_id INTEGER NOT NULL REFERENCES carts(id) ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            variant_id INTEGER REFERENCES product_variants(id) ON DELETE SET NULL,
            variant_name TEXT,
            quantity INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            discount_type TEXT NOT NULL,
            discount_value INTEGER NOT NULL,
            min_order_amount INTEGER DEFAULT 0,
            max_discount INTEGER DEFAULT 0,
            usage_limit INTEGER DEFAULT 0,
            times_used INTEGER DEFAULT 0,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            customer_phone TEXT,
            subtotal INTEGER NOT NULL,
            discount_amount INTEGER DEFAULT 0,
            tax_amount INTEGER DEFAULT 0,
            total_amount INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT DEFAULT 'PENDING',
            fulfillment_status TEXT DEFAULT 'PENDING',
            voucher_id INTEGER REFERENCES vouchers(id) ON DELETE SET NULL,
            voucher_code TEXT,
            internal_notes TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
            variant_id INTEGER,
            variant_name TEXT,
            product_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            subtotal INTEGER NOT NULL,
            digital_payload TEXT
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            transaction_id TEXT UNIQUE NOT NULL,
            gateway TEXT NOT NULL,
            payment_type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL,
            raw_response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS store_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            group_name TEXT DEFAULT 'general',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_email TEXT,
            action TEXT NOT NULL,
            resource_type TEXT,
            resource_id TEXT,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
        CREATE INDEX IF NOT EXISTS idx_products_slug ON products(slug);
        CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
        CREATE INDEX IF NOT EXISTS idx_product_variants_prod ON product_variants(product_id);
        CREATE INDEX IF NOT EXISTS idx_product_images_product ON product_images(product_id);
        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
        CREATE INDEX IF NOT EXISTS idx_orders_number ON orders(order_number);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(payment_status);
        CREATE INDEX IF NOT EXISTS idx_license_keys_product ON license_keys(product_id, is_used);
        CREATE INDEX IF NOT EXISTS idx_cart_items_cart ON cart_items(cart_id);
        """)

        # Safe schema migration for existing databases
        for col, tbl in [("variant_id", "cart_items"), ("variant_name", "cart_items"), ("variant_id", "order_items"), ("variant_name", "order_items")]:
            try:
                conn.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} TEXT;")
            except Exception:
                pass

def get_setting(key: str, default: str = "") -> str:
    try:
        with get_db() as conn:
            row = conn.execute("SELECT value FROM store_settings WHERE key = ?", (key,)).fetchone()
            return row["value"] if row and row["value"] is not None else default
    except Exception:
        return default

def set_setting(key: str, value: str, group_name: str = "general"):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO store_settings (key, value, group_name, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                group_name = excluded.group_name,
                updated_at = CURRENT_TIMESTAMP
        """, (key, value, group_name))

def get_all_settings() -> dict:
    try:
        with get_db() as conn:
            rows = conn.execute("SELECT key, value FROM store_settings").fetchall()
            return {r["key"]: r["value"] for r in rows}
    except Exception:
        return {}

def log_audit(user_id: int, user_email: str, action: str, resource_type: str = None, resource_id: str = None, details: str = None, ip_address: str = None, conn = None):
    try:
        sql = """
            INSERT INTO audit_logs (user_id, user_email, action, resource_type, resource_id, details, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (user_id, user_email, action, resource_type, str(resource_id) if resource_id else None, details, ip_address)
        if conn:
            conn.execute(sql, params)
        else:
            with get_db() as c:
                c.execute(sql, params)
    except Exception as e:
        print(f"Error logging audit: {e}")
