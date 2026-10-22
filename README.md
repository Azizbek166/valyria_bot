# 🔥 "OLD VALERIYA" (ASOIAF) TELEGRAM RPG BOT

Qadimgi Valeriya (ASOIAF / Game of Thrones) olamidagi 52 ta xonadon kurashiga asoslangan Telegram RPG o'yin boti.

---

## 📌 Asosiy Xususiyatlar va Mexanikalar

1. **52 ta Xonadon (Har bir xonadonga faqat 1 ta o'yinchi):**
   - **1 – 40:** Quruqlik xonadonlari (Targaryen, Velaryon, Celtigar...)
   - **41 – 52:** Dengiz Lordlari (Nyzarys, Volnorys, Aethyron...)
   - Bir o'yinchi xonadonni band qilgandan so'ng, uni boshqa hech kim ololmaydi.
2. **Harbiy Tizim:**
   - **Oddiy askar**: 1 tanga (Hujum: 1, Himoya: 1)
   - **Chakra**: 2 tanga (Hujum: 2, Himoya: 2)
   - **Tilla plash**: 3 tanga (Hujum: 3, Himoya: 3)
   - **Oʻrgimchak 🕷**: 300 tanga (Hujum: 500, Himoya: 500)
   - **Ajdar 🐲**: 400 tanga (C-daraja: 500 ball)
     - C -> B: 150 tanga (1000 ball)
     - B -> A: 150 tanga (1500 ball)
     - A -> S: 150 tanga (2000 ball - maksimal)
3. **❄️ Ajdarlarning 3 Kunlik Muzlashi:**
   - Ajdar har bir jangda qatnashgach **aniq 3 kunga (72 soat) muzlaydi**.
   - Muzlagan ajdar ushbu vaqt mobaynida janglarda qatnasha olmaydi va kuchga qo'shilmaydi.
4. **⚔️ Janglar va Vassal Qilish:**
   - Mag'lub bo'lgan xonadon g'olibning **VASSALIGA** aylanadi!
   - G'olib mag'lub xazinadan 20% oltinni o'lja sifatida oladi.
   - Hukmdor o'z vassallaridan muntazam soliq yig'ib boradi.
5. **Panellar va Bo'limlar:**
   - `🌋 Oila tanlash` — 52 ta xonadondan birini tanlash
   - `👤 Profil` — Xonadon, armiya, ajdarlar va vassallar
   - `🛕 Uylar` — Barcha xonadonlar holati
   - `🏞 Valeria Ekspiditsya` — 1, 4, 8 soatlik qidiruv va oltin topish
   - `🏦 Golden` — Kunlik bonus va oltin o'tkazmalari
   - `⚔️ Janglar` — Hujum qilish va vassal qilish
   - `🐉 Hayvonlarim 🕷` — Ajdarlar va o'rgimchaklar boshqaruvi
   - `✨ Soliqlar` — Vassallardan soliq yig'ish
   - `🥇 Reyting` — Eng kuchli va boy Lordlar
   - `🛘 Hududiy topshiriqlar` — Quests va mukofotlar
   - `👑 Admin paneli` — ID `7009689119` uchun maxsus boshqaruv

---

## 🚀 1. Kompyuterda Lokal Ishga Tushirish

1. Terminalda loyiha papkasiga kiring:
   ```bash
   cd valyria_bot
   ```
2. Kerakli kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
3. Botni ishga tushiring:
   ```bash
   python bot.py
   ```

---

## 🌐 2. Botni BEPUL va QOTMAYDIGAN Serverga Joylash (24/7 Hosting)

Bot uzluksiz (24/7) ishlashi uchun uni bepul bulutli serverga (Render yoki Koyeb) joylashtirish tavsiya etiladi.

### Variant A: Render.com (Tavsiya etiladi)

1. **GitHub** akkauntingizga ushbu `valyria_bot` papkasidagi kodlarni yuklang (yangi repository ochib).
2. [Render.com](https://render.com) saytiga kiring va GitHub orqali ro'yxatdan o'ting.
3. **New +** tugmasini bosing va **Background Worker** (yoki Web Service) bo'limini tanlang.
4. O'zingizning GitHub repository'ingizni ulang.
5. Sozlamalarni quyidagicha to'ldiring:
   - **Name**: `valyria-rpg-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Plan**: `Free`
6. **Environment Variables** bo'limiga quyidagini qo'shing:
   - `BOT_TOKEN`: `8817691077:AAEy2vSoWfJ3PjT7ARNKCoMLqlW4FwVyDjs`
7. **Create Background Worker** tugmasini bosing.
   Bot 1-2 daqiqada ishga tushadi va 24/7 rejimida qotmasdan ishlaydi!

---

### Variant B: Koyeb.com

1. [Koyeb.com](https://koyeb.com) ga kiring.
2. **Create App** tugmasini bosing.
3. GitHub repository'ingizni tanlang.
4. Koyeb avtomatik ravishda `Dockerfile` ni taniydi.
5. Environment variable sifatida `BOT_TOKEN` ni kiriting.
6. **Deploy** tugmasini bosing.

---

### Variant C: Railway.app

1. [Railway.app](https://railway.app) ga kiring.
2. **New Project** -> **Deploy from GitHub repo** tanlang.
3. Variables bo'limiga `BOT_TOKEN` qo'shing.
4. Ishga tushirish avtomatik amalga oshadi!
