"""Parol hash + sessiya boshqaruvi (stdlib, qo'shimcha kutubxonasiz)."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import database

PBKDF2_ITERATIONS = 200_000
SESSION_TTL_DAYS = 30


def _now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """(pass_hash, pass_salt) qaytaradi. salt berilmasa yangi yaratiladi."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), PBKDF2_ITERATIONS
    )
    return dk.hex(), salt


def verify_password(password: str, pass_hash: str, pass_salt: str) -> bool:
    calc, _ = hash_password(password, pass_salt)
    return hmac.compare_digest(calc, pass_hash)


def create_user(login: str, name: str, password: str, role: str = "ombor",
                phone: str | None = None, position: str | None = None,
                status: str = "active") -> int:
    pass_hash, pass_salt = hash_password(password)
    now = _now().isoformat()
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (login, name, phone, position, role, "
        "pass_hash, pass_salt, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (login, name, phone, position, role, pass_hash, pass_salt, status, now, now),
    )
    uid = cur.lastrowid
    conn.commit()
    conn.close()
    return uid


def get_user_by_login(login: str):
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE login = ?", (login,))
    row = cur.fetchone()
    conn.close()
    return row


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    now = _now()
    expires = now + timedelta(days=SESSION_TTL_DAYS)
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) "
        "VALUES (?, ?, ?, ?)",
        (token, user_id, now.isoformat(), expires.isoformat()),
    )
    conn.commit()
    conn.close()
    return token


def resolve_session(token: str):
    """Token bo'yicha foydalanuvchi qatorini qaytaradi yoki None (muddati o'tgan/yo'q)."""
    if not token:
        return None
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT u.*, s.expires_at FROM sessions s "
        "JOIN users u ON u.id = s.user_id WHERE s.token = ?",
        (token,),
    )
    row = cur.fetchone()
    if row is None:
        conn.close()
        return None
    try:
        expired = datetime.fromisoformat(row["expires_at"]) < _now()
    except Exception:
        expired = True
    if expired or row["status"] != "active":
        cur.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        return None
    conn.close()
    return row


def delete_session(token: str) -> None:
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def user_public(row) -> dict:
    """Parol maydonlarisiz xavfsiz user dict."""
    return {
        "id": row["id"],
        "login": row["login"],
        "name": row["name"],
        "phone": row["phone"],
        "position": row["position"],
        "role": row["role"],
        "status": row["status"],
    }
