# 🚀 VPS Deploy Handoff — Sfatshop Mini App Backend (eskiz.uz)
> Yaratildi: 2026-06-25 | Davom: Claude Code | Render o'rniga VPS

## 🎯 VAZIFA (Claude Code uchun)
Sfatshop Mini App backend'ini eskiz.uz VPS'ga deploy qilish.
Python + nginx (reverse proxy) + HTTPS (Let's Encrypt) + systemd (doim ishlash).
FAQAT Sfatshop (Attendance bot hozircha Render'da qoladi, TEGILMAYDI).

## 🖥️ SERVER MA'LUMOTLARI
- Provayder: eskiz.uz (VPS 2: 2 yadro, 2 GB RAM, 40 GB NVMe, Ubuntu 24.04)
- IP: 45.138.158.174
- Port: 22
- Login: root
- Parol: foydalanuvchida (chatga yozilmaydi — SSH so'roviga user kiritadi)
- Ulanish: ssh root@45.138.158.174

## ⚠️ MUHIM — XAVFSIZLIK
- Parol chatga YOZILMAYDI. Claude Code SSH ulanganda user paroldan foydalanadi.
- Sozlash boshida: yangi sudo user yaratish + SSH key + root parol login o'chirish (ixtiyoriy, tavsiya).
- UFW firewall: faqat 22 (SSH), 80 (HTTP), 443 (HTTPS) ochiq.

## 📦 LOYIHA FAYLLARI (mahalliy: /Users/jb89/Desktop/Sfatshop/backend/)
- app.py          — aiohttp REST API (PORT env'dan, CORS *)
- sync.py         — Uzum 2 dokondan DB ga (254 mahsulot)
- database.py     — SQLite, DB_PATH env'dan (os.getenv("DB_PATH","shop.db"))
- uzum_client.py  — Uzum API (token apiKey, Bearer YO'Q)
- requirements.txt — aiohttp==3.14.1, httpx==0.28.1, python-dotenv==1.2.2
- .env            — UZUM_TOKEN, ADMIN_TOKEN (git'ga YUKLANMAGAN)

## 📋 ENDPOINTLAR (eslatma)
- GET  /                         health
- GET  /api/products             (public) aktiv mahsulotlar
- GET  /api/admin/uzum-products  (admin) sync'langan + in_mini_app
- GET  /api/admin/mini-products  (admin) mini app dagi barcha
- POST /api/admin/products       (admin) qo'shish
- PATCH /api/admin/products/{id} (admin)
- DELETE /api/admin/products/{id}(admin)
- POST /api/admin/sync           (admin) Uzum yangilash

## 🪜 DEPLOY QADAMLARI (Claude Code bajaradi)

### 1. Serverga ulanish va tayyorlash
```
ssh root@45.138.158.174
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip nginx git ufw certbot python3-certbot-nginx
```

### 2. Firewall
```
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable
```

### 3. Kod yuklash
- GitHub orqali: git clone https://github.com/jaloliddinbahriddinov444-Sfatshop/Sfatshop.git
  (backend/ papkasi kerak; .env GitHubda yo'q — qo'lda yaratiladi)
- /opt/sfatshop/ ga joylashtirish tavsiya etiladi

### 4. Python muhit
```
cd /opt/sfatshop/backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

### 5. .env yaratish (server'da, qo'lda)
- UZUM_TOKEN, ADMIN_TOKEN — mahalliy backend/.env dan ko'chiriladi
- DB_PATH=/opt/sfatshop/backend/shop.db
- PORT=8000

### 6. systemd service (doim ishlash uchun) — /etc/systemd/system/sfatshop.service
- venv/bin/python app.py ni ishga tushiradi
- Avtoматик qayta ishga tushadi (Restart=always)
- systemctl enable --now sfatshop

### 7. nginx reverse proxy
- domen yoki IP'ni 127.0.0.1:8000 ga yo'naltirish
- /etc/nginx/sites-available/sfatshop

### 8. HTTPS (Let's Encrypt)
- DOMEN KERAK (pastga qarang)
- certbot --nginx -d api.DOMEN.uz
- Avtomatik yangilanadi

### 9. Birinchi sync
- curl yoki admin panel orqali POST /api/admin/sync → 254 mahsulot

## 🌐 DOMEN (HAL QILINDI)
- sfatshop.uz — FAOL, Eskiz orqali, amal 25-Jun-2027
- NS: ns1..ns4.eskiz.uz
- Backend URL: https://api.sfatshop.uz
- DNS A-record: api → 45.138.158.174 (user Eskiz panelida qo'shmoqda)

## 🔗 DEPLOY'DAN KEYIN (URL yangilash)
- index.html → BACKEND_URL = https://api.sfatshop.uz → commit/push
- sfatshop_ombor_22.html → Mini App bo'limida "Backend manzili" → https://api.sfatshop.uz
- GitHub Pages allaqachon yoqilgan (mini app frontend)

## 👤 USER USLUBI
- Uzbek (Lotin); SODDA tushuntirish — user dasturchi emas
- Bitta komanda har blokda; shell'da Uzbek apostrof YO'Q
- Parol/token MAXFIY — chatga yozilmaydi
- Har qadamni test qilib, tasdiqlab oldinga
- plan -> confirm -> patch
