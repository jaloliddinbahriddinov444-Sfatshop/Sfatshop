from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import database
import uzum_client


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _map_card(shop_id: int, card: dict) -> dict:
    sku_list = card.get("skuList") or []
    first = sku_list[0] if sku_list else {}
    sku_id = first.get("skuId")
    return {
        "shop_id": shop_id,
        "product_id": str(card.get("productId")),
        "sku_id": str(sku_id) if sku_id is not None else None,
        "name": card.get("title") or "",
        "category": card.get("category"),
        "image_url": card.get("image") or card.get("previewImg"),
        "stock": card.get("quantityActive") or 0,
        "uzum_price": first.get("price"),
        "raw_json": json.dumps(card, ensure_ascii=False),
    }

_UPSERT_SQL = """
INSERT INTO uzum_products
    (shop_id, product_id, sku_id, name, category,
     image_url, stock, uzum_price, raw_json, fetched_at)
VALUES
    (:shop_id, :product_id, :sku_id, :name, :category,
     :image_url, :stock, :uzum_price, :raw_json, :fetched_at)
ON CONFLICT(shop_id, product_id) DO UPDATE SET
    sku_id     = excluded.sku_id,
    name       = excluded.name,
    category   = excluded.category,
    image_url  = excluded.image_url,
    stock      = excluded.stock,
    uzum_price = excluded.uzum_price,
    raw_json   = excluded.raw_json,
    fetched_at = excluded.fetched_at
"""

async def sync_shop(shop_id: int) -> dict:
    database.init_db()
    conn = database.get_connection()
    cur = conn.cursor()
    result = {"shop_id": shop_id, "status": "error", "count": 0, "message": "unknown"}
    try:
        cards = await uzum_client.get_all_products(shop_id)
        now = _now()
        rows = [{**_map_card(shop_id, c), "fetched_at": now} for c in cards]
        if rows:
            cur.executemany(_UPSERT_SQL, rows)
        conn.commit()
        result = {"shop_id": shop_id, "status": "ok",
                  "count": len(rows), "message": None}
    except uzum_client.UzumClientError as exc:
        conn.rollback()
        result = {"shop_id": shop_id, "status": "error", "count": 0,
                  "message": f"{type(exc).__name__}: {exc}"}
    except Exception as exc:
        conn.rollback()
        result = {"shop_id": shop_id, "status": "error", "count": 0,
                  "message": f"Unexpected: {exc}"}
    finally:
        cur.execute(
            "INSERT INTO sync_log "
            "(shop_id, action, status, message, products_updated, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (shop_id, "sync_shop", result["status"],
             result["message"], result["count"], _now()),
        )
        conn.commit()
        conn.close()
    return result

async def sync_all(shop_ids: list[int], delay: float = 1.0) -> list[dict]:
    results = []
    for i, sid in enumerate(shop_ids):
        results.append(await sync_shop(sid))
        if i < len(shop_ids) - 1:
            await asyncio.sleep(delay)
    return results


if __name__ == "__main__":
    SHOPS = [17042, 111637]
    for r in asyncio.run(sync_all(SHOPS)):
        print(r)