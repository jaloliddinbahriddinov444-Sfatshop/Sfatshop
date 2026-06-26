"""Bitta admin foydalanuvchini yaratadi. Parol ENV'dan olinadi (kodda turmaydi).

Ishlatish (parol ekranga chiqmaydi, git'ga tushmaydi):
    ADMIN_LOGIN=admin ADMIN_NAME="Direktor" ADMIN_PASSWORD='...' \
        ./venv/bin/python seed_admin.py

Agar login allaqachon mavjud bo'lsa — paroli yangilanadi (qayta ishga tushirsa bo'ladi).
"""
import getpass
import os
import sys

from dotenv import load_dotenv

import auth
import database

load_dotenv()  # DB_PATH va boshqalar .env'dan olinsin


def main() -> int:
    login = (os.getenv("ADMIN_LOGIN") or "admin").strip()
    name = (os.getenv("ADMIN_NAME") or "Admin").strip()
    password = os.getenv("ADMIN_PASSWORD") or ""
    if not password:
        # Interaktiv: parol ekranda ko'rinmaydi
        password = getpass.getpass("Yangi admin paroli: ")
        confirm = getpass.getpass("Parolni qayta kiriting: ")
        if password != confirm:
            print("XATO: parollar mos kelmadi.", file=sys.stderr)
            return 1
    if len(password) < 6:
        print("XATO: parol kamida 6 belgi bo'lsin.", file=sys.stderr)
        return 1
    database.init_db()
    existing = auth.get_user_by_login(login)
    if existing is not None:
        ph, ps = auth.hash_password(password)
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET pass_hash=?, pass_salt=?, name=?, role='admin', "
            "status='active', updated_at=? WHERE login=?",
            (ph, ps, name, auth._now().isoformat(), login),
        )
        cur.execute("DELETE FROM sessions WHERE user_id=?", (existing["id"],))
        conn.commit()
        conn.close()
        print(f"Admin '{login}' yangilandi (parol o'rnatildi).")
    else:
        uid = auth.create_user(login, name, password, role="admin")
        print(f"Admin '{login}' yaratildi (id={uid}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
