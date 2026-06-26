# 🏗️ Sfatshop Mini App — Uzum Integratsiya Rejasi

> Uzum Seller'dagi kartochkalarni qo'lda tanlab, Mini App'ga avtomatik o'tkazish tizimi

---

## 1. Asosiy g'oya (bir jumlada)

Siz admin panelda Uzum'dagi barcha mahsulotlarni ko'rasiz → **qaysilarini Mini App'ga chiqarishni belgilasiz** → tanlanganlar avtomatik tortib olinadi va xaridorlarga ko'rsatiladi. Qoldiq (stock) avtomatik yangilanib turadi.

---

## 2. Sizning talablaringiz (tasdiqlangan)

| Talab | Qaror |
|-------|-------|
| Yangilanish chastotasi | Xaridorga qulay → qoldiq tez-tez avtomat yangilanadi |
| Ko'rsatiladigan ma'lumot | Rasm, nomi, tasnif, qoldiq (Uzum'dan) |
| Video | ⚠️ Uzum API'da YO'Q → admin qo'lda qo'shadi |
| Narx | Admin o'zi belgilaydi (Uzum narxi emas) |
| 5 do'kon | Qo'lda tanlash — qaysi kartochka o'tishini admin belgilaydi |

---

## 3. Uzum API'dan nima olamiz

Topilgan asosiy endpoint:

```
GET /v1/product/shop/{shopId}?page=0&size=50
→ Do'kondagi barcha mahsulotlar (sahifalab)
```

Har bir kartochkada (`SellerProductCard`):

| Maydon | Mini App'da ishlatiladimi? |
|--------|---------------------------|
| productId | ✅ ID sifatida |
| title | ✅ Nomi |
| image, previewImg | ✅ Rasm |
| category | ✅ Tasnif |
| skuList[].characteristics | ✅ Xususiyatlar (rang, o'lcham) |
| quantityActive | ✅ Qoldiq |
| skuList[].price | ⚙️ Ma'lumot uchun (lekin admin o'zi narx qo'yadi) |

Qoldiq yangilash uchun:
```
GET /v3/fbs/sku/stocks → SKU qoldiqlari (sahifalab)
```

---

## 4. Arxitektura (umumiy rasm)

```
┌─────────────────────────────────────────────┐
│              UZUM SELLER API                  │
│         api-seller.uzum.uz                    │
│   (5 do'kon: 81957, 7739, 79198, 17042, ...)  │
└──────────────────┬────────────────────────────┘
                   │ GET /v1/product/shop/{id}
                   │ (Authorization: token)
                   ▼
┌─────────────────────────────────────────────┐
│           RENDER BACKEND (Python)             │
│   (mavjud attendance-bot service kengaytma)   │
│                                               │
│  ┌─────────────┐    ┌──────────────────────┐ │
│  │ Uzum klient │───▶│   SQLite (shop.db)    │ │
│  │ (httpx)     │    │  - uzum_products      │ │
│  └─────────────┘    │  - mini_app_products  │ │
│                     │  - sync_log           │ │
│  ┌─────────────────────────────────────────┐ │
│  │  REST API                                │ │
│  │  GET  /api/products    (Mini App uchun)  │ │
│  │  GET  /api/admin/uzum   (barcha mahsulot)│ │
│  │  POST /api/admin/select (kartochka tanla)│ │
│  │  POST /api/admin/sync   (qoldiq yangila) │ │
│  └─────────────────────────────────────────┘ │
└──────────┬──────────────────────┬─────────────┘
           │                      │
           ▼                      ▼
┌──────────────────┐   ┌────────────────────────┐
│   ADMIN PANEL     │   │   MINI APP (xaridor)    │
│  (kartochka       │   │   index.html            │
│   tanlash +       │   │   fetch /api/products   │
│   narx + video)   │   │   → katalog ko'rsatadi  │
└──────────────────┘   └────────────────────────┘
```

---

## 5. Ma'lumotlar bazasi (SQLite)

### Jadval 1: `uzum_products` (Uzum'dan kelgan xom ma'lumot)
```sql
CREATE TABLE uzum_products (
    product_id     INTEGER PRIMARY KEY,
    shop_id        INTEGER NOT NULL,
    title          TEXT,
    category       TEXT,
    image          TEXT,
    preview_img    TEXT,
    quantity       INTEGER DEFAULT 0,
    uzum_price     INTEGER,
    characteristics TEXT,    -- JSON
    raw_json       TEXT,     -- to'liq nusxa
    updated_at     TEXT
);
```

### Jadval 2: `mini_app_products` (admin tanlagan + sozlagan)
```sql
CREATE TABLE mini_app_products (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id   INTEGER NOT NULL,   -- uzum_products ga bog'liq
    shop_id      INTEGER NOT NULL,
    is_active    INTEGER DEFAULT 1,  -- Mini App'da ko'rinadimi
    custom_price INTEGER,            -- admin qo'ygan narx
    video_url    TEXT,               -- admin qo'shgan video
    sort_order   INTEGER DEFAULT 0,
    added_at     TEXT,
    UNIQUE(product_id)
);
```

### Jadval 3: `sync_log` (yangilanishlar tarixi)
```sql
CREATE TABLE sync_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    shop_id    INTEGER,
    synced_at  TEXT,
    status     TEXT,
    count      INTEGER
);
```

---

## 6. Ish oqimi (3 bosqich)

### Bosqich A — Uzum'dan tortib olish (admin: "Yangilash" bosadi)
```
1. Backend har 5 do'kon uchun GET /v1/product/shop/{id}
2. Kelgan mahsulotlar → uzum_products jadvaliga saqlanadi
3. sync_log ga yoziladi
```

### Bosqich B — Admin tanlovi (qo'lda)
```
1. Admin panel barcha uzum_products ni ko'rsatadi
2. Admin "Mini App'ga chiqar" tugmasini bosadi
3. Narx qo'yadi + (ixtiyoriy) video URL qo'shadi
4. → mini_app_products ga yoziladi
```

### Bosqich C — Xaridor ko'radi (avtomatik)
```
1. Mini App ochiladi → fetch /api/products
2. Faqat is_active=1 mahsulotlar qaytadi
3. Narx = custom_price, qoldiq = uzum_products.quantity (yangi)
```

---

## 7. Qoldiqni yangilab turish

Xaridorga qulay bo'lishi uchun:

```
Variant 1 (oddiy):  Admin "Yangilash" bossa → qoldiq yangilanadi
Variant 2 (avto):   Render Cron Job → har 30 daqiqada avtomat
```

**Tavsiya:** Boshida Variant 1, keyin Variant 2 ga o'tamiz.

---

## 8. Xavfsizlik

| Element | Yechim |
|---------|--------|
| Uzum token | Render → Environment Variables (kodda EMAS) |
| Admin panel | Parol / Telegram auth bilan himoya |
| API token oqib ketishi | `.env`, `.gitignore` — GitHub'ga tushmasin |

⚠️ **Eslatma:** Uzum o'zi ogohlantirgan — token ochiq joyga tushsa, avtomatik o'chiriladi. Shuning uchun faqat Render maxfiy o'zgaruvchisida saqlaymiz.

---

## 9. Bosqichma-bosqich qurish rejasi

```
[1] DB schema yaratish (3 jadval)           → sql-pro
[2] Uzum API klient (httpx + token)         → python-pro
[3] Sync funksiya (5 do'kon → DB)           → backend-developer
[4] REST API (/api/products, /api/admin/*)  → backend-developer
[5] Admin panel (kartochka tanlash UI)      → (HTML, Claude o'zi)
[6] Mini App'ni fetch'ga ulash              → (HTML, Claude o'zi)
[7] Test + xatolarni tuzatish               → debugger
[8] Token xavfsizligini tekshirish          → code-reviewer
```

---

## 10. Ochiq savollar (keyingi qadamda hal qilamiz)

1. Admin panelni alohida sahifa qilaymizmi yoki Mini App ichida?
2. Render'da yangi service yoki mavjud attendance-bot kengaytmasimi?
3. Avtomatik qoldiq yangilash (Cron) qachondan boshlaymiz?

---

*Tayyorladi: Claude | Sfatshop loyihasi | 2026-yil iyun*
