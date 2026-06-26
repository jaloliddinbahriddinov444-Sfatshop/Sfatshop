"""Bitta admin foydalanuvchini yaratadi. Parol ENV'dan olinadi (kodda turmaydi).

Ishlatish (parol ekranga chiqmaydi, git'ga tushmaydi):
    ADMIN_LOGIN=admin ADMIN_NAME="Direktor" ADMIN_PASSWORD='...' \
        ./venv/bin/python seed_admin.py

Agar login allaqachon mavjud bo'lsa — paroli yangilanadi (qayta ishga tushirsa bo'ladi).
"""
import os
import sys

import auth
import database


def main() -> int:
    login = (os.getenv("ADMIN_LOGIN") or "admin").strip()
    name = (os.getenv("ADMIN_NAME") or "Admin").strip()
    password = os.getenv("ADMIN_PASSWORD") or ""
    if not password:
        print("XATO: ADMIN_PASSWORD env o'rnatilmagan.", file=sys.stderr)
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
