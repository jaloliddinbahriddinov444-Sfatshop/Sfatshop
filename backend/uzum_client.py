from __future__ import annotations

import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()
UZUM_TOKEN: str | None = os.getenv("UZUM_TOKEN")

_BASE_URL = "https://api-seller.uzum.uz/api/seller-openapi"
_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)
_PRODUCT_FIELDS = (
    "productId", "title", "category", "image", "previewImg", "quantityActive", "skuList"
)


class UzumClientError(Exception):
    pass


class UzumAuthError(UzumClientError):
    pass


class UzumForbiddenError(UzumClientError):
    pass


class UzumAPIError(UzumClientError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


class UzumTimeoutError(UzumClientError):
    pass


class UzumNetworkError(UzumClientError):
    pass


def _extract_items(body: Any) -> list[dict]:
    # Documented Uzum shape: {"productList": [...], "totalProductsAmount": N}.
    # Check top-level productList FIRST; keep defensive fallbacks for other shapes.
    if isinstance(body, list):
        return body
    if not isinstance(body, dict):
        return []
    direct = body.get("productList")
    if isinstance(direct, list):
        return direct
    for key in ("content", "items", "list", "cards", "results", "data"):
        val = body.get(key)
        if isinstance(val, list):
            return val
    for outer_key in ("payload", "data", "result"):
        outer = body.get(outer_key)
        if isinstance(outer, dict):
            for inner_key in ("productList", "content", "items", "list", "cards", "results"):
                inner = outer.get(inner_key)
                if isinstance(inner, list):
                    return inner
    return []


async def get_products(shop_id: int, page: int = 0, size: int = 50) -> dict:
    if not UZUM_TOKEN:
        raise UzumAuthError("UZUM_TOKEN not set in environment")

    headers = {
        "Authorization": UZUM_TOKEN,
        "Content-Type": "application/json",
    }
    url = f"{_BASE_URL}/v1/product/shop/{shop_id}"
    params = {"page": page, "size": size}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, headers=headers) as client:
            response = await client.get(url, params=params)
    except httpx.TimeoutException as exc:
        raise UzumTimeoutError(str(exc)) from exc
    except httpx.RequestError as exc:
        raise UzumNetworkError(str(exc)) from exc

    if response.status_code == 401:
        raise UzumAuthError("Uzum API returned 401 — token is wrong or expired")
    if response.status_code == 403:
        raise UzumForbiddenError("Uzum API returned 403 — access forbidden")
    if not response.is_success:
        raise UzumAPIError(response.status_code, response.text)

    return response.json()


async def get_all_products(shop_id: int) -> list[dict]:
    size = 50
    all_items: list[dict] = []
    page = 0

    while True:
        body = await get_products(shop_id, page=page, size=size)
        total = body.get("totalProductsAmount", 0) if isinstance(body, dict) else 0
        items = _extract_items(body)

        for card in items:
            all_items.append({k: card.get(k) for k in _PRODUCT_FIELDS})

        if not items or len(all_items) >= total:
            break

        page += 1

    return all_items
