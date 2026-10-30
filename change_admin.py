#!/usr/bin/env python3
"""
PRIME APPS — CLI Tool: Ubah Email & Password Admin
Memperbarui kredensial superadmin langsung di basis data webstore.db.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
bootstrap_path = BASE_DIR / "bootstrap.py"
if bootstrap_path.exists():
    with open(bootstrap_path) as bf:
        exec(bf.read(), globals())

from app.database import get_db
from app.security import hash_password

def change_admin():
    print("=" * 55)
    print("🔐 PRIME APPS — GANTI EMAIL & PASSWORD ADMIN")
    print("=" * 55)

    with get_db() as conn:
        admin_row = conn.execute("SELECT id, email, full_name, role FROM users WHERE role IN ('superadmin', 'admin') ORDER BY id ASC LIMIT 1").fetchone()
        if not admin_row:
            print("❌ Akun administrator tidak ditemukan di basis data.")
            return

        print(f"Akun admin saat ini : {admin_row['email']} ({admin_row['full_name']})")
        print("-" * 55)

        try:
            new_email = input(f"Masukkan Email Baru [{admin_row['email']}]: ").strip()
            if not new_email:
                new_email = admin_row['email']

            new_password = input("Masukkan Password Baru: ").strip()
            if not new_password:
                print("❌ Password baru tidak boleh kosong.")
                return

            if len(new_password) < 6:
                print("❌ Password baru minimal harus 6 karakter.")
                return

            new_hash = hash_password(new_password)
            conn.execute(
                "UPDATE users SET email = ?, password_hash = ? WHERE id = ?",
                (new_email.lower(), new_hash, admin_row['id'])
            )

        except (KeyboardInterrupt, EOFError):
            print("\n❌ Dibatalkan oleh pengguna.")
            return

    print("=" * 55)
    print("✅ BERHASIL! Kredensial admin telah diperbarui:")
    print(f"   Email Baru    : {new_email.lower()}")
    print(f"   Password Baru : {new_password}")
    print(f"   Login URL     : http://localhost:8000/admin/login")
    print("=" * 55)

if __name__ == "__main__":
    change_admin()
