from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from aiohttp import web
from dotenv import load_dotenv

import auth
import database
import sync as sync_mod

load_dotenv()
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
DEFAULT_SHOPS = [17042, 111637]

# Auth talab qilinmaydigan ochiq yo'llar
PUBLIC_PATHS = {"/", "/api/products", "/api/login"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rows(cur) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]

@web.middleware
async def cors_mw(request, handler):
    if request.method == "OPTIONS":
        resp = web.Response(status=204)
    else:
        try:
            resp = await handler(request)
        except web.HTTPException as exc:
            resp = exc
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Admin-Token, X-Session-Token"
    return resp


def _identify(request):
    """So'rov egasini aniqlaydi.

    Qaytaradi: dict {role, user, is_service} yoki None (auth yo'q).
    - X-Admin-Token == ADMIN_TOKEN  -> xizmat (Mini App + cron), role=admin
    - X-Session-Token amal qiladigan -> shu foydalanuvchi o'z roli bilan
    """
    admin_tok = request.headers.get("X-Admin-Token")
    if ADMIN_TOKEN and admin_tok == ADMIN_TOKEN:
        return {"role": "admin", "user": None, "is_service": True}
    sess_tok = request.headers.get("X-Session-Token")
    if sess_tok:
        row = auth.resolve_session(sess_tok)
        if row is not None:
            return {"role": row["role"], "user": row, "is_service": False}
    return None


@web.middleware
async def admin_auth_mw(request, handler):
    if request.method == "OPTIONS" or request.path in PUBLIC_PATHS:
        return await handler(request)
    needs_auth = (
        request.path.startswith("/api/admin")
        or request.path in ("/api/me", "/api/logout")
    )
    if needs_auth:
        ident = _identify(request)
        if ident is None:
            return web.json_response({"error": "unauthorized"}, status=401)
        request["identity"] = ident
    return await handler(request)


def _require_role(request, *roles):
    """Ruxsat bo'lmasa HTTPForbidden ko'taradi. Xizmat tokeni doimo o'tadi."""
    ident = request.get("identity") or {}
    if ident.get("is_service"):
        return
    if ident.get("role") not in roles:
        raise web.HTTPForbidden(
            text=json.dumps({"error": "forbidden"}),
            content_type="application/json",
        )

async def get_products(request: web.Request) -> web.Response:
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT m.id AS mini_id, u.product_id, u.name, u.category, "
        "u.image_url, u.stock, m.price, m.video_url "
        "FROM mini_app_products m "
        "JOIN uzum_products u ON u.id = m.uzum_product_id "
        "WHERE m.is_active = 1 "
        "ORDER BY m.added_at DESC"
    )
    data = _rows(cur)
    conn.close()
    return web.json_response({"products": data, "count": len(data)})


async def admin_uzum_products(request: web.Request) -> web.Response:
    shop_id = request.query.get("shop_id")
    q = request.query.get("q")
    sql = (
        "SELECT u.id, u.shop_id, u.product_id, u.name, u.category, "
        "u.image_url, u.stock, u.uzum_price, "
        "CASE WHEN m.id IS NULL THEN 0 ELSE 1 END AS in_mini_app "
        "FROM uzum_products u "
        "LEFT JOIN mini_app_products m ON m.uzum_product_id = u.id "
    )
    where, params = [], []
    if shop_id:
        where.append("u.shop_id = ?")
        params.append(int(shop_id))
    if q:
        where.append("u.name LIKE ?")
        params.append(f"%{q}%")
    if where:
        sql += "WHERE " + " AND ".join(where) + " "
    sql += "ORDER BY u.id DESC LIMIT 500"
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    data = _rows(cur)
    conn.close()
    return web.json_response({"products": data, "count": len(data)})

async def admin_mini_products(request: web.Request) -> web.Response:
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT m.id AS mini_id, u.product_id, u.name, u.image_url, u.stock, "
        "m.price, m.video_url, m.is_active "
        "FROM mini_app_products m "
        "JOIN uzum_products u ON u.id = m.uzum_product_id "
        "ORDER BY m.added_at DESC"
    )
    data = _rows(cur)
    conn.close()
    return web.json_response({"products": data, "count": len(data)})


async def admin_add_product(request: web.Request) -> web.Response:
    _require_role(request, "admin")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    uzum_id = body.get("uzum_product_id")
    price = body.get("price")
    video_url = body.get("video_url")
    if uzum_id is None or price is None:
        return web.json_response(
            {"error": "uzum_product_id va price majburiy"}, status=400)
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM uzum_products WHERE id = ?", (uzum_id,))
    if cur.fetchone() is None:
        conn.close()
        return web.json_response({"error": "uzum_product topilmadi"}, status=404)
    cur.execute(
        "SELECT id FROM mini_app_products WHERE uzum_product_id = ?", (uzum_id,))
    if cur.fetchone() is not None:
        conn.close()
        return web.json_response({"error": "allaqachon qoshilgan"}, status=409)
    now = _now()
    cur.execute(
        "INSERT INTO mini_app_products "
        "(uzum_product_id, price, video_url, is_active, added_at, updated_at) "
        "VALUES (?, ?, ?, 1, ?, ?)",
        (uzum_id, price, video_url, now, now),
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return web.json_response({"id": new_id, "status": "added"}, status=201)

async def admin_update_product(request: web.Request) -> web.Response:
    _require_role(request, "admin")
    pid = int(request.match_info["id"])
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    fields, params = [], []
    for key in ("price", "video_url", "is_active"):
        if key in body:
            fields.append(f"{key} = ?")
            params.append(body[key])
    if not fields:
        return web.json_response(
            {"error": "ozgartirish uchun maydon yoq"}, status=400)
    fields.append("updated_at = ?")
    params.append(_now())
    params.append(pid)
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE mini_app_products SET {', '.join(fields)} WHERE id = ?", params)
    conn.commit()
    changed = cur.rowcount
    conn.close()
    if changed == 0:
        return web.json_response({"error": "topilmadi"}, status=404)
    return web.json_response({"id": pid, "status": "updated"})


async def admin_delete_product(request: web.Request) -> web.Response:
    _require_role(request, "admin")
    pid = int(request.match_info["id"])
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM mini_app_products WHERE id = ?", (pid,))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    if changed == 0:
        return web.json_response({"error": "topilmadi"}, status=404)
    return web.json_response({"id": pid, "status": "deleted"})

async def admin_sync(request: web.Request) -> web.Response:
    _require_role(request, "admin")
    shops = DEFAULT_SHOPS
    try:
        body = await request.json()
        if isinstance(body, dict) and body.get("shop_ids"):
            shops = [int(s) for s in body["shop_ids"]]
    except Exception:
        pass
    results = await sync_mod.sync_all(shops)
    return web.json_response({"results": results})


async def admin_get_wh_state(request: web.Request) -> web.Response:
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT data, updated_at FROM wh_state WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    if row is None:
        return web.json_response({"data": None, "updated_at": None})
    return web.json_response({"data": row["data"], "updated_at": row["updated_at"]})


async def admin_put_wh_state(request: web.Request) -> web.Response:
    _require_role(request, "admin", "ombor")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    data = body.get("data")
    base = body.get("base")
    if data is None:
        return web.json_response({"error": "data majburiy"}, status=400)
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False)
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT updated_at FROM wh_state WHERE id = 1")
    row = cur.fetchone()
    if row is not None and base != row["updated_at"]:
        conn.close()
        return web.json_response(
            {"error": "conflict", "current_updated_at": row["updated_at"]},
            status=409)
    now = _now()
    if row is None:
        cur.execute(
            "INSERT INTO wh_state (id, data, updated_at) VALUES (1, ?, ?)",
            (data, now))
    else:
        cur.execute(
            "UPDATE wh_state SET data = ?, updated_at = ? WHERE id = 1",
            (data, now))
    conn.commit()
    conn.close()
    return web.json_response({"status": "saved", "updated_at": now})


# ------------------------- Auth (sessiya) -------------------------

async def login(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    login_val = (body.get("login") or "").strip()
    password = body.get("password") or ""
    if not login_val or not password:
        return web.json_response({"error": "login va password majburiy"}, status=400)
    row = auth.get_user_by_login(login_val)
    if row is None or row["status"] != "active" or \
            not auth.verify_password(password, row["pass_hash"], row["pass_salt"]):
        return web.json_response({"error": "login yoki parol notogri"}, status=401)
    token = auth.create_session(row["id"])
    return web.json_response({"token": token, "user": auth.user_public(row)})


async def logout(request: web.Request) -> web.Response:
    tok = request.headers.get("X-Session-Token")
    if tok:
        auth.delete_session(tok)
    return web.json_response({"status": "logged_out"})


async def me(request: web.Request) -> web.Response:
    ident = request.get("identity") or {}
    if ident.get("is_service"):
        return web.json_response({"user": {"role": "admin", "name": "Service",
                                           "is_service": True}})
    return web.json_response({"user": auth.user_public(ident["user"])})


# ------------------------- Foydalanuvchi boshqaruvi (admin) ----------

async def admin_list_users(request: web.Request) -> web.Response:
    _require_role(request, "admin")
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, login, name, phone, position, role, status, "
        "created_at, updated_at FROM users ORDER BY id")
    data = _rows(cur)
    conn.close()
    return web.json_response({"users": data, "count": len(data)})


async def admin_create_user(request: web.Request) -> web.Response:
    _require_role(request, "admin")
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    login_val = (body.get("login") or "").strip()
    name = (body.get("name") or "").strip()
    password = body.get("password") or ""
    role = body.get("role") or "ombor"
    if not login_val or not name or not password:
        return web.json_response(
            {"error": "login, name, password majburiy"}, status=400)
    if role not in ("admin", "ombor", "hisobot"):
        return web.json_response({"error": "notogri role"}, status=400)
    if auth.get_user_by_login(login_val) is not None:
        return web.json_response({"error": "login band"}, status=409)
    uid = auth.create_user(
        login_val, name, password, role=role,
        phone=body.get("phone"), position=body.get("position"),
        status=body.get("status") or "active",
    )
    return web.json_response({"id": uid, "status": "created"}, status=201)


async def admin_update_user(request: web.Request) -> web.Response:
    _require_role(request, "admin")
    uid = int(request.match_info["id"])
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    fields, params = [], []
    for key in ("name", "phone", "position", "role", "status", "login"):
        if key in body:
            if key == "role" and body[key] not in ("admin", "ombor", "hisobot"):
                return web.json_response({"error": "notogri role"}, status=400)
            fields.append(f"{key} = ?")
            params.append(body[key])
    if "password" in body and body["password"]:
        ph, ps = auth.hash_password(body["password"])
        fields.append("pass_hash = ?")
        params.append(ph)
        fields.append("pass_salt = ?")
        params.append(ps)
    if not fields:
        return web.json_response({"error": "ozgartirish uchun maydon yoq"}, status=400)
    fields.append("updated_at = ?")
    params.append(_now())
    params.append(uid)
    conn = database.get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", params)
    except database.sqlite3.IntegrityError:
        conn.close()
        return web.json_response({"error": "login band"}, status=409)
    conn.commit()
    changed = cur.rowcount
    # parol/rol/status o'zgarsa, eski sessiyalarni bekor qil
    if any(k in body for k in ("password", "status", "role")):
        cur.execute("DELETE FROM sessions WHERE user_id = ?", (uid,))
        conn.commit()
    conn.close()
    if changed == 0:
        return web.json_response({"error": "topilmadi"}, status=404)
    return web.json_response({"id": uid, "status": "updated"})


async def admin_delete_user(request: web.Request) -> web.Response:
    _require_role(request, "admin")
    uid = int(request.match_info["id"])
    ident = request.get("identity") or {}
    cur_user = ident.get("user")
    if cur_user is not None and cur_user["id"] == uid:
        return web.json_response({"error": "ozingizni ochira olmaysiz"}, status=400)
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM users WHERE role='admin' AND status='active'")
    admin_count = cur.fetchone()["c"]
    cur.execute("SELECT role, status FROM users WHERE id = ?", (uid,))
    target = cur.fetchone()
    if target is None:
        conn.close()
        return web.json_response({"error": "topilmadi"}, status=404)
    if target["role"] == "admin" and target["status"] == "active" and admin_count <= 1:
        conn.close()
        return web.json_response(
            {"error": "oxirgi adminni ochira olmaysiz"}, status=400)
    cur.execute("DELETE FROM sessions WHERE user_id = ?", (uid,))
    cur.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()
    return web.json_response({"id": uid, "status": "deleted"})


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


def create_app() -> web.Application:
    database.init_db()
    app = web.Application(
        middlewares=[cors_mw, admin_auth_mw],
        client_max_size=20 * 1024 * 1024,
    )
    app.router.add_get("/", health)
    app.router.add_get("/api/products", get_products)
    app.router.add_get("/api/admin/uzum-products", admin_uzum_products)
    app.router.add_get("/api/admin/mini-products", admin_mini_products)
    app.router.add_post("/api/admin/products", admin_add_product)
    app.router.add_patch("/api/admin/products/{id}", admin_update_product)
    app.router.add_delete("/api/admin/products/{id}", admin_delete_product)
    app.router.add_post("/api/admin/sync", admin_sync)
    app.router.add_get("/api/admin/wh-state", admin_get_wh_state)
    app.router.add_put("/api/admin/wh-state", admin_put_wh_state)
    # Auth (sessiya)
    app.router.add_post("/api/login", login)
    app.router.add_post("/api/logout", logout)
    app.router.add_get("/api/me", me)
    # Foydalanuvchi boshqaruvi (admin)
    app.router.add_get("/api/admin/users", admin_list_users)
    app.router.add_post("/api/admin/users", admin_create_user)
    app.router.add_patch("/api/admin/users/{id}", admin_update_user)
    app.router.add_delete("/api/admin/users/{id}", admin_delete_user)
    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    web.run_app(create_app(), host="0.0.0.0", port=port)
