# CLAUDE CODE — Sfatshop backend yaxshilash vazifalari
> Tayyorlandi: 2026-06-25 | Bajaruvchi: Claude Code (terminal: Mac jb89 + VPS SSH)
> Til: Uzbek (lotin). Bu hujjat butun ish rejasini bosqichma-bosqich beradi.

## 0. Umumiy qoidalar (MAJBURIY)
- Uslub: plan -> confirm -> patch. Har bosqichdan oldin nima qilishingni qisqa ayt,
  foydalanuvchi tasdiqlasin, keyin bajar.
- Maxfiylik: ADMIN_TOKEN, Uzum API key, Telegram bot token HECH QACHON ekranga yoki
  kodga yozilmaydi. Ular faqat .env / serverdagi env faylda turadi. echo qilma.
- VPS o'zgarishlari: avval mavjud holatni ANIQLA (backend papkasi, venv yo'li,
  systemd service nomi, DB yo'li), keyin tegil. Hech narsani ko'r-ko'rona o'chirma.
- Shell buyruqlarda Uzbek apostrof ISHLATMA. Bitta mantiqiy qadam = bitta blok.
- SSH parolini foydalanuvchi o'zi kiritadi. Kutib tur, so'rama.
- O'zgartirishdan oldin tegishli faylni o'qib chiq.

## 1. Mavjud tizim (kontekst)
- Backend JONLI: https://api.sfatshop.uz (aiohttp + SQLite + nginx + certbot + systemd)
- VPS: 45.138.158.174 (Ubuntu 24.04), SSH: ssh root@45.138.158.174 (port 22)
- Lokal backend (dev nusxa): /Users/jb89/Desktop/Sfatshop/backend/
  app.py, database.py, sync.py, uzum_client.py, .env, shop.db
- Admin panel (Mac, brauzerda ochiladi): /Users/jb89/Downloads/sfatshop_ombor_22.html
  - Backend manzili input id: ma-backend ; localStorage key: sfatshop_ma_backend
- Repo: github.com/jaloliddinbahriddinov444-Sfatshop/Sfatshop
- Jadvallar: uzum_products, mini_app_products(is_active), sync_log
- Ishlaydigan do'konlar: 17042, 111637

### API (mavjud — o'zgartirish shart emas)
- GET   /                          -> {"status":"ok"} (health)
- GET   /api/products              -> public, faqat is_active=1
- GET   /api/admin/uzum-products   -> ?shop_id= ?q=   (qidiruv + filtr ALLAQACHON bor)
- GET   /api/admin/mini-products   -> is_active bilan qaytaradi
- POST  /api/admin/products        -> {uzum_product_id, price, video_url?}  (dup -> 409)
- PATCH /api/admin/products/{id}   -> {price?, video_url?, is_active?}  (is_active ALLAQACHON bor)
- DELETE /api/admin/products/{id}
- POST  /api/admin/sync            -> {shop_ids?} default [17042,111637]
- Admin endpointlar: X-Admin-Token header majburiy.

MUHIM: qidiruv (q), filtr (shop_id), is_active toggle uchun BACKEND TAYYOR.
Faza 3 — faqat panel (HTML) ishi, backend tegilmaydi.

---

## FAZA 1 — Xato va xavfsizlik (avval shu)

### Vazifa 1.1 — Panelда "VPS / Lokal" tugma (faqat HTML, Mac)
Maqsad: Backend manzili default https://api.sfatshop.uz bo'lsin va qayerga yozayotgani
aniq ko'rinsin. localhost xatosi qaytmasin.
Fayl: /Users/jb89/Downloads/sfatshop_ombor_22.html
Qilish:
1) ma-backend input default qiymatini https://api.sfatshop.uz qil. localStorage
   sfatshop_ma_backend bo'sh bo'lsa shu default ishlatilsin.
2) Input yoniga 2 tugma: [VPS] -> https://api.sfatshop.uz , [Lokal] -> http://localhost:8000
   (qiymatni inputga yozadi + localStorage'ga saqlaydi).
3) Badge: manzil api.sfatshop.uz bo'lsa yashil "VPS ulangan", localhost bo'lsa qizil
   "LOKAL (ehtiyot bo'l)".
Tekshirish: panelni qayta och -> badge yashil; [Lokal] bossang qizilga o'tadi.

### Vazifa 1.2 — shop.db avtomatik backup (VPS)
Maqsad: har kuni DB nusxasi olinsin, oxirgi 14 kun saqlansin.
Qilish (SSH 45.138.158.174):
1) DB yo'lini topib ol: VPS .env dagi DB_PATH yoki systemd service WorkingDirectory.
2) /root/sfatshop-backups/ papka yarat.
3) Skript: sqlite3 .backup yoki gzip nusxa -> shop_YYYY-MM-DD fayl;
   14 kundan eski fayllarni o'chir.
4) systemd timer (yoki cron) kunlik 02:30 da ishga tushir.
Tekshirish: skriptni qo'lda 1 marta ishga tushir -> backups papkada bugungi fayl paydo bo'lsin.
(Ixtiyoriy: nusxani Telegram'ga ham yuborish — 2.2 dagi token bilan.)

---

## FAZA 2 — Avtomatlashtirish

### Vazifa 2.1 — Avtomatik kunlik sync (VPS)
Maqsad: qoldiq + Uzum narxi har kuni o'zi yangilansin.
DIQQAT: custom narx (mini_app_products.price) TEGILMAYDI — sync faqat uzum_products ni yangilaydi.
Tavsiya etilgan usul (bitta yozuvchi, xavfsiz): ishlayotgan API'ni chaqir:
  curl -s -X POST https://api.sfatshop.uz/api/admin/sync -H "X-Admin-Token: $TOKEN"
  (TOKEN ni VPS .env dan o'qi, ekranga chiqarma)
Qilish:
1) Kichik skript: .env dan ADMIN_TOKEN o'qiydi, yuqoridagi curl, natijani logga yozadi.
2) systemd timer kunlik 03:00.
Zaxira usul (agar API localhost'dan ko'rinmasa): venv ichida "python sync.py" (backend papkada, .env bilan).
Tekshirish: qo'lda ishga tushir -> javobda results; sync_log jadvalida yangi satr.

### Vazifa 2.2 — Health monitoring -> Telegram (VPS)
Maqsad: API o'lib qolsa (GET / != 200), foydalanuvchiga Telegram'ga xabar kelsin.
Foydalanuvchidan kerak: bot tokeni + chat id (o'zi beradi/serverga kiritadi).
Qilish:
1) Skript: http_code ni tekshir; 200 bo'lmasa Telegram sendMessage. Token serverdagi env faylda.
2) systemd timer (yoki cron) har 5 daqiqada.
3) Ketma-ket xato bo'lsa ham 1 marta ogohlantir (flag fayl) — spam bo'lmasin.
Tekshirish: qo'lda ishga tushir -> 200; vaqtincha noto'g'ri URL bilan sinab, xabar kelishini ko'r.

---

## FAZA 3 — Panel qulayligi (faqat HTML, Mac; backend tayyor)

Fayl: /Users/jb89/Downloads/sfatshop_ombor_22.html

### Vazifa 3.1 — Qidiruv + filtr + ko'p tanlash
Maqsad: 256 mahsuldan tez topib, bir nechtasini birga chiqarish.
Qilish:
1) Uzum mahsulotlar ro'yxatiga: qidiruv inputi (-> /api/admin/uzum-products?q=),
   do'kon filtri (?shop_id=17042 / 111637).
2) Har qatorda checkbox. Tanlanganlar uchun bitta narx maydoni YOKI "+%" ustama.
3) "Tanlanganlarni chiqarish" tugmasi -> har biriga POST /api/admin/products.
   409 (allaqachon bor) bo'lsa o'tkazib yubor; oxirida xulosa: n ta qo'shildi.
Tekshirish: qidiruv ishlaydi; 3 ta belgilab chiqar -> /api/products da paydo bo'lsin.

### Vazifa 3.2 — Yoqish/o'chirish tugma (is_active)
Maqsad: jonli mahsulotni 1 tugma bilan vaqtincha o'chirib/yoqib qo'yish.
Qilish: "Jonli mahsulotlar" ro'yxatida har qatorga toggle ->
  PATCH /api/admin/products/{id} {"is_active": 0 yoki 1}. Holatni rang bilan ko'rsat.
Tekshirish: o'chir -> /api/products dan yo'qoladi; yoq -> qaytadi.

---

## Foydalanuvchidan kerak bo'ladigan narsalar
- SSH parol (VPS) — o'zi kiritadi.
- Telegram ogohlantirish (Vazifa 2.2): bot tokeni + chat id — o'zi beradi/serverga kiritadi.
  (Mavjud attendance botdan foydalanish yoki yangi "alert" bot ochish — foydalanuvchi tanlaydi.)

## Tavsiya etilgan tartib
1.1 -> 1.2 -> 2.1 -> 2.2 -> 3.1 -> 3.2
Har vazifadan keyin "Tekshirish" mezonini bajar va foydalanuvchiga qisqa hisobot ber.

## Eslatma (ish bilan bog'liq emas, lekin muhim)
- VPS muddati: 25.07.2026 (yangilash kerak).
- Domen muddati: 25.06.2027.
