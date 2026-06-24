# 🚀 Render Deploy Handoff — Sfatshop Mini App Backend
> Yaratildi: 2026-06-24 | Davom: Claude Code

## 🎯 VAZIFA (Claude Code uchun)
Sfatshop Mini App backend'ini Render'ga deploy qilish (YANGI alohida service).
Keyin frontend URL'larni yangilash va GitHub Pages yoqish.

## ✅ TAYYOR (shu bosqichgacha qilingan, mahalliy localhost:8000 da test qilingan)
- backend/database.py — 3 jadval (uzum_products, mini_app_products, sync_log)
  DB_PATH endi env'dan: os.getenv("DB_PATH", "shop.db")
- backend/uzum_client.py — Uzum API; _extract_items() productList ni birinchi tekshiradi
- backend/sync.py — 2 dokondan 254 mahsulot DB ga (UPSERT + sync_log)
- backend/app.py — aiohttp REST API, X-Admin-Token himoya, CORS *, PORT env'dan
- backend/requirements.txt — aiohttp==3.14.1, httpx==0.28.1, python-dotenv==1.2.2
- sfatshop_ombor_22.html — "Mini App" admin bo'limi (qo'shish/tahrir/o'chirish/sync)
- index.html — backendga ulangan (loadProducts → /api/products, BACKEND_URL const)

## 📋 ENDPOINTLAR
- GET    /                          health
- GET    /api/products              (public) aktiv mahsulotlar
- GET    /api/admin/uzum-products   (admin)  sync'langan barcha + in_mini_app flag
- GET    /api/admin/mini-products   (admin)  mini app dagi barcha (aktiv+noaktiv)
- POST   /api/admin/products        (admin)  {uzum_product_id, price, video_url}
- PATCH  /api/admin/products/{id}   (admin)  {price | video_url | is_active}
- DELETE /api/admin/products/{id}   (admin)
- POST   /api/admin/sync            (admin)  Uzum'dan yangilash

## 🔧 RENDER SOZLAMALARI (eng muhim qism!)
- YANGI Web Service yaratish — attendance-bot ga TEGILMAYDI (u: srv-d8d7unho3t8c73e9idh0)
- Root Directory: backend
- Build Command: pip install -r requirements.txt
- Start Command: python app.py   (PORT env'dan o'qiladi — app.py da tayyor)
- Python: 3.11+ (kod 3.14 da yozilgan, 3.11+ mos)
- PERSISTENT DISK (MUHIM — bo'lmasa qo'shilgan mahsulotlar har deploy'da o'chadi):
  - Disk qo'shish, Mount Path: /data
- Environment Variables (Render dashboard'da qo'lda kiritiladi):
  - UZUM_TOKEN   = <backend/.env dagi qiymat>
  - ADMIN_TOKEN  = <backend/.env dagi qiymat>
  - DB_PATH      = /data/shop.db
  - (PORT — Render o'zi beradi, qo'lda kerakmas)

## 🪜 DEPLOY QADAMLARI
1. git add backend/ index.html RENDER_DEPLOY_HANDOFF.md → commit → push
   DIQQAT: .env push QILINMAYDI (.gitignore da). Tokenlar Render dashboard'da qo'lda kiritiladi.
2. Render'da yangi Web Service, GitHub repo ulash, yuqoridagi sozlamalar
3. Persistent disk (/data) + env vars qo'shish
4. Deploy → URL olish (masalan https://sfatshop-backend.onrender.com)
5. Birinchi sync: admin panel orqali "Uzumdan yangilash" yoki POST /api/admin/sync

## 🔗 DEPLOY'DAN KEYIN
- index.html → BACKEND_URL ni Render URL ga o'zgartirish → commit → push
- sfatshop_ombor_22.html → Mini App bo'limida "Backend manzili" ni Render URL ga (UI orqali)
- [8] GitHub Pages yoqish: repo Settings > Pages > Branch: main, /(root) → public havola tayyor

## ⚠️ E'TIBOR
- Uzum token: "Authorization" header, apiKey, Bearer PREFIKSI YO'Q
- Ishlaydigan 2 dokon: 17042, 111637 (81957/7739/79198 → 403)
- Render free tier 15 daq harakatsizlikdan keyin "uxlaydi" — birinchi so'rov sekin (~30s)
- CORS hozir * — keyin faqat GitHub Pages domeniga cheklash mumkin (ixtiyoriy)

## 👤 USER USLUBI
- Uzbek (Lotin); plan → confirm → patch; bitta komanda har blokda
- SODDAROQ tushuntirish — user dasturchi emas, atamalardan kam foydalanish
- Token MAXFIY — chatga yozilmaydi (.env yoki Render dashboard'da)
- shell bloklarda Uzbek apostrof YOQ
- Mac yo'l: /Users/jb89/Desktop/Sfatshop/
