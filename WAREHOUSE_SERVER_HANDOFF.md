# Ombor paneli → Serverga ko'chirildi (blob-sync)
> Yangilandi: 2026-06-26 | Davom: Claude Code

## Nima qilindi
Ombor paneli (mahsulot/kirim-chiqim/hodim/joy) endi **localStorage o'rniga serverda** saqlanadi.
Usul: butun `state` JSON sifatida bitta yozuvga saqlanadi (blob-sync) — to'liq CRUD emas.
Sabab: panelning o'nlab funksiyasini qayta yozmaslik, xavfsiz va tez.

## Backend (VPS: 45.138.158.174, /opt/sfatshop/backend)
- database.py — yangi jadval:
  `wh_state(id=1, data TEXT, updated_at TEXT)` — shop.db ichida, kunlik 02:30 backupga kiradi.
- app.py — 2 ta endpoint (admin token bilan himoyalangan):
  - GET  /api/admin/wh-state  -> {data, updated_at}
  - PUT  /api/admin/wh-state  -> {data, base}; agar base != serverdagi updated_at -> 409 (versiya himoyasi)
- CORS ga PUT qo'shildi; client_max_size = 20 MB.
- O'zgarish VPS git tarixiga commit qilingan: 21e9faa (main).
  Lekin GitHub'ga (origin) HALI push qilinmagan + Mac lokal repo ESKI.

## Panel (/Users/jb89/Downloads/sfatshop_ombor_22.html)
- loadState/saveState serverga ulandi:
  - whLoad() — login'dan keyin serverdan yuklaydi (eski bloated localStorage o'chiriladi).
  - saveState() — debounce (0.7s) bilan PUT qiladi.
  - 409 (konflikt) -> yuqorida qizil banner "Sahifani yangilang".
- Backend URL + admin token "Mini App" bo'limidagi maydonlardan olinadi
  (localStorage: sfatshop_ma_backend, sfatshop_ma_token) — Mini App bilan bir xil token.
- HAR BRAUZERDA bir marta admin token kiritilishi shart (Mini App > Saqlash).

## Multi-user
- "Oxirgi saqlash + versiya himoyasi": ikki kishi bir vaqtda saqlasa, kechikkani 409 oladi
  va sahifani yangilashga undaydi (ma'lumot o'chmaydi).

## Qoldi (keyingi ish)
- [x] GitHub'ga push (2026-06-26): VPS 21e9faa origin'ga ketdi (cherry-pick -> 0488279),
      Mac+VPS+GitHub sinxron. Mac terminal ruxsati endi ishlaydi.
- [x] FAZA D: haqiqiy backend login (sessiya) — BAJARILDI, jonli deploy + brauzerда tasdiqlandi.
      Backend: users+sessions jadval, pbkdf2 hash, /api/login,/logout,/me, /api/admin/users (admin),
      middleware X-Admin-Token(xizmat) YOKI X-Session-Token(rol bilan). ADMIN_TOKEN xizmat tokeni bo'lib qoldi.
      Panel (ombor.html, repo'da): login->/api/login (haqiqiy <form>, autocomplete=username/current-password),
      ombor sessiya tokeni bilan, Hodimlar->/api/admin/users (server). Brauzerда jonli login ISHLADI.
      Admin seed qilindi (login: admin). Brend favicon qo'shildi.
- [x] HOSTING: panel nginx orqali https://api.sfatshop.uz/panel da (location = /panel -> /opt/sfatshop/ombor.html).
      nginx config: /etc/nginx/sites-available/sfatshop (zaxira: sfatshop.bak.20260626).
      Panel yangilanishi: Mac'da tahrir -> commit/push -> VPS 'cd /opt/sfatshop && git pull' (statik, restart shart emas).
- [ ] Ixtiyoriy: ombor.sfatshop.uz subdomen (DNS A: ombor->45.138.158.174 kerak, keyin certbot).
- [ ] Eski jasur/malika va boshqa hodimlarni Hodimlar sahifasidan qayta yaratish (serverда faqat 1 admin).
- [ ] FAZA E (kelajak): import/eksport, hisobotlar va h.k.

## Deploy shpargalkasi (FAZA D dan keyin)
- Backend o'zgarsa: Mac commit/push -> VPS `cd /opt/sfatshop && git pull && systemctl restart sfatshop.service`.
- Panel (ombor.html) o'zgarsa: Mac commit/push -> VPS `git pull` (restart shart emas, nginx statik beradi).
- Yangi admin/parol reset: VPS `cd /opt/sfatshop/backend && ADMIN_LOGIN=.. ./venv/bin/python seed_admin.py` (parol getpass).
- SSH parolsiz (kalit bilan) ishlaydi: ssh root@45.138.158.174.

## Eslatma
- VPS muddati: 25.07.2026 | Domen: 25.06.2027
- Performans: panelda render 400 mahsulot bilan cheklangan (muzlamaslik uchun) + O(n) guruhlash.
- Yangi server holati toza boshlandi (default 6 demo mahsulot; eski Uzum-import axlati ko'chmadi).
