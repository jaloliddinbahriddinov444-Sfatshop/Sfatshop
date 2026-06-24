# Sfatshop Mini App - Uzum Integratsiya Rejasi

## Asosiy goya
Admin Uzum dagi mahsulotlarni korib, qaysilarini Mini App ga
chiqarishni qolda tanlaydi. Tanlanganlar avtomatik tortib olinadi.
Narx va video admin tomonidan qoshiladi. Qoldiq Uzum dan avtomat.

## Qarorlar (tasdiqlangan)
- Backend: YANGI alohida Render service
- Admin panel: alohida sahifa (admin.html)
- Malumot: rasm, nomi, tasnif, qoldiq (Uzum API dan)
- Narx: admin ozi belgilaydi
- Video: Uzum API da YOQ, admin qolda qoshadi
- Kartochka: admin qolda tanlaydi

## Uzum API endpointlar
- GET /v1/product/shop/{shopId}?page=0&size=50  -> mahsulotlar royxati
- GET /v3/fbs/sku/stocks                          -> qoldiqlar
- POST /v1/product/{shopId}/sendPriceData         -> narx ozgartirish

## Dokon ID lari
81957, 7739, 79198, 17042, 111637

## DB jadvallar (SQLite - shop.db)
1. uzum_products    -> Uzum dan kelgan xom malumot
2. mini_app_products -> admin tanlagan + narx/video
3. sync_log         -> yangilanishlar tarixi

## Qurilish tartibi
[1] DB schema (3 jadval)         - sql-pro
[2] Uzum API klient (httpx)      - python-pro
[3] Sync funksiya (5 dokon)      - backend-developer
[4] REST API endpointlar         - backend-developer
[5] Admin sahifa (tanlash UI)    - HTML
[6] Mini App ni fetch ga ulash   - HTML
[7] Test va debug                - debugger
[8] Xavfsizlik tekshiruvi        - code-reviewer

## Xavfsizlik
Uzum token -> Render Environment Variables (kodda EMAS)
.env fayl -> .gitignore ga qoshilsin

## Texnologiya
Python 3.11, aiohttp, SQLite, Render, httpx
