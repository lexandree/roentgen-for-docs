import asyncio
import logging
from aiogram import Bot, Dispatcher
from src.bot.config import settings
from src.bot.services.auth import auth_service
from src.bot.handlers.messages import router as messages_router
from src.bot.handlers.images import router as images_router

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    # Sync whitelist on startup
    auth_service.sync_whitelist()

    # Include routers (Order matters: photo handler first)
    dp.include_router(images_router)
    dp.include_router(messages_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())