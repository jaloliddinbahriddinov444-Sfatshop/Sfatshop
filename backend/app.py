from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from aiohttp import web
from dotenv import load_dotenv

import database
import sync as sync_mod

load_dotenv()
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
DEFAULT_SHOPS = [17042, 111637]


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
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Admin-Token"
    return resp


@web.middleware
async def admin_auth_mw(request, handler):
    if request.path.startswith("/api/admin") and request.method != "OPTIONS":
        token = request.headers.get("X-Admin-Token")
        if not ADMIN_TOKEN or token != ADMIN_TOKEN:
            return web.json_response({"error": "unauthorized"}, status=401)
    return await handler(request)

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
    return app


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    web.run_app(create_app(), host="0.0.0.0", port=port)
