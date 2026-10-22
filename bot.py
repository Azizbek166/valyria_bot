import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import init_db

# Handlers
from handlers.start import router as start_router
from handlers.profile import router as profile_router
from handlers.houses import router as houses_router
from handlers.beasts import router as beasts_router
from handlers.battles import router as battles_router
from handlers.taxes import router as taxes_router
from handlers.expeditions import router as expeditions_router
from handlers.bank import router as bank_router
from handlers.tasks import router as tasks_router
from handlers.admin import router as admin_router
from handlers.essos import router as essos_router
from handlers.map_view import router as map_router
from handlers.green_bank import router as green_bank_router
from handlers.castle import router as castle_router
from handlers.alliance import router as alliance_router

import os
from aiohttp import web

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def start_health_server():
    """Bulutli bepul serverlar (Render, Koyeb va h.k.) 24/7 uxlab qolmasligi uchun health-check veb serveri"""
    app = web.Application()
    async def handle_ping(request):
        return web.Response(text="🔥 Valyria RPG Bot is active and running 24/7! 🐉")

    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"24/7 Keep-alive veb-serveri {port}-portda ishga tushdi.")

async def main():
    logger.info("Valyria RPG Bot ishga tushmoqda...")

    # Baza jadvallarini yaratish va 52 ta xonadonni yuklash
    await init_db()
    logger.info("Ma'lumotlar bazasi initsializatsiya qilindi.")

    # 24/7 keep-alive serverini yoqish
    try:
        await start_health_server()
    except Exception as e:
        logger.warning(f"Health server ishga tushmadi (lokal rejim): {e}")

    # Bot va Dispatcher sozlash
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    # Routerlarni ulash
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(houses_router)
    dp.include_router(map_router)
    dp.include_router(green_bank_router)
    dp.include_router(castle_router)
    dp.include_router(alliance_router)
    dp.include_router(beasts_router)
    dp.include_router(battles_router)
    dp.include_router(taxes_router)
    dp.include_router(expeditions_router)
    dp.include_router(bank_router)
    dp.include_router(tasks_router)
    dp.include_router(admin_router)
    dp.include_router(essos_router)

    # Eski kutilayotgan yangilanishlarni o'tkazib yuborish
    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("Bot tayyor va so'rovlarni qabul qilmoqda!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
