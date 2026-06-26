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
- [~] FAZA D: haqiqiy backend login (sessiya) — BAJARILDI va jonli deploy qilindi (ee93420, 7c1c76d, 3c0c8cb).
      Backend: users+sessions jadval, pbkdf2 hash, /api/login,/logout,/me, /api/admin/users (admin),
      middleware X-Admin-Token(xizmat) YOKI X-Session-Token(rol bilan). ADMIN_TOKEN xizmat tokeni bo'lib qoldi.
      Panel (ombor.html, endi repo'da): login->/api/login, ombor sessiya tokeni bilan, Hodimlar->/api/admin/users.
      Jonli smoke test: login 200 + wh-state GET 200 + blob JSON OK.
      QOLDI (foydalanuvchi tasdiqlashi): (1) jonli admin seed (seed_admin.py, parol o'zi kiritadi);
      (2) panelni brauzerда ochib login sinash (DOM brauzerда hali ishlamagan — Chrome kengaytma ulanmagan edi);
      (3) hosting joyi tanlash. ESLATMA: jonli'da hozir 0 user — eski jasur/malika qayta yaratilishi shart.
- [ ] FAZA E (kelajak): har hodimni jonli serverga ko'chirish / hosting.

## Eslatma
- VPS muddati: 25.07.2026 | Domen: 25.06.2027
- Performans: panelda render 400 mahsulot bilan cheklangan (muzlamaslik uchun) + O(n) guruhlash.
- Yangi server holati toza boshlandi (default 6 demo mahsulot; eski Uzum-import axlati ko'chmadi).
