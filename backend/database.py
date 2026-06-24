import sqlite3

import os
DB_PATH = os.getenv("DB_PATH", "shop.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS uzum_products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id     INTEGER NOT NULL,
            product_id  TEXT    NOT NULL,
            sku_id      TEXT,
            name        TEXT    NOT NULL,
            category    TEXT,
            image_url   TEXT,
            stock       INTEGER DEFAULT 0,
            uzum_price  REAL,
            raw_json    TEXT,
            fetched_at  TEXT    NOT NULL,
            UNIQUE(shop_id, product_id)
        );

        CREATE TABLE IF NOT EXISTS mini_app_products (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            uzum_product_id   INTEGER NOT NULL REFERENCES uzum_products(id),
            price             REAL    NOT NULL,
            video_url         TEXT,
            is_active         INTEGER DEFAULT 1,
            added_at          TEXT    NOT NULL,
            updated_at        TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sync_log (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id          INTEGER,
            action           TEXT    NOT NULL,
            status           TEXT    NOT NULL,
            message          TEXT,
            products_updated INTEGER DEFAULT 0,
            created_at       TEXT    NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_uzum_products_shop_id
            ON uzum_products(shop_id);

        CREATE INDEX IF NOT EXISTS idx_uzum_products_product_id
            ON uzum_products(product_id);

        CREATE INDEX IF NOT EXISTS idx_mini_app_products_uzum_product_id
            ON mini_app_products(uzum_product_id);

        CREATE INDEX IF NOT EXISTS idx_sync_log_created_at
            ON sync_log(created_at);
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
