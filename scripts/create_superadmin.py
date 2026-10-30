#!/usr/bin/env python3
"""
CLI script to securely create or update a Superadmin account.
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, PROJECT_ROOT)
try:
    import sitecustomize
except Exception:
    pass

from app.database import get_db, init_db, log_audit
from app.security import hash_password

def main():
    if len(sys.argv) < 3:
        print("Penggunaan: python3 scripts/create_superadmin.py <email> <password> \"<nama_lengkap>\" [no_telepon]")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else "Super Administrator"
    phone = sys.argv[4] if len(sys.argv) > 4 else "+62 812-3456-7890"

    init_db()
    pwd_hash = hash_password(password)

    with get_db() as conn:
        existing = conn.execute("SELECT id, role FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.execute("""
                UPDATE users 
                SET password_hash = ?, full_name = ?, phone = ?, role = 'superadmin', status = 'active', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (pwd_hash, full_name, phone, existing["id"]))
            user_id = existing["id"]
            print(f"✓ Pengguna '{email}' berhasil diperbarui menjadi Superadmin!")
        else:
            cursor = conn.execute("""
                INSERT INTO users (email, password_hash, full_name, phone, role, status)
                VALUES (?, ?, ?, ?, 'superadmin', 'active')
            """, (email, pwd_hash, full_name, phone))
            user_id = cursor.lastrowid
            print(f"✓ Akun Superadmin baru '{email}' berhasil dibuat dengan ID {user_id}!")

    log_audit(user_id, email, "SUPERADMIN_BOOTSTRAPPED", "users", str(user_id), "Superadmin dibuat/diperbarui via CLI script")

if __name__ == "__main__":
    main()
