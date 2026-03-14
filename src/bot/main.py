import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from src.bot.config import settings
from src.bot.services.auth import auth_service
from src.bot.handlers.messages import router as messages_router
from src.bot.handlers.images import router as images_router

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=settings.telegram_bot_token)
    
    # Configure FSM Storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Sync whitelist on startup
    auth_service.sync_whitelist()

    # Include routers (Order matters: photo handler first)
    dp.include_router(images_router)
    dp.include_router(messages_router)

    from aiogram.types import BotCommand
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="status", description="Статус воркеров и текущей сессии"),
        BotCommand(command="model", description="Выбрать воркер для обычного диалога"),
        BotCommand(command="analyze", description="Запустить пакетный (batch) анализ"),
        BotCommand(command="clear", description="Очистить контекст и память VRAM"),
        BotCommand(command="end", description="Завершить сессию (то же, что /clear)"),
    ])

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())