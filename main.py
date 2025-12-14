import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import TELEGRAM_BOT_TOKEN
from bot.handlers import router
from bot.edit_handlers import edit_router
from bot.advanced_handlers import router as advanced_router
from database.db import init_db
from core.scheduler import scheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Инициализация базы данных...")
    init_db()

    logger.info("Запуск планировщика...")
    scheduler.start()

    logger.info("Запуск бота...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(advanced_router)
    dp.include_router(edit_router)
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)

    logger.info("✅ Бот запущен и готов к работе!")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.stop()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")