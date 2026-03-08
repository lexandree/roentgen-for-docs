from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from src.bot.services.auth import auth_service
from src.bot.services.api_client import api_client
from src.bot.states import AnalysisSession
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
from typing import Dict

router = Router()

album_tasks: Dict[int, asyncio.Task] = {}

def get_single_image_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="⚡️ Локально (GTX 1060)", callback_data="route_local")
    builder.button(text="📦 В очередь (Colab)", callback_data="route_colab")
    builder.button(text="🧠 Глубоко (RunPod)", callback_data="route_runpod")
    builder.adjust(1)
    return builder.as_markup()

def get_batch_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📦 Пакетный анализ (Colab)", callback_data="route_colab")
    builder.button(text="🧠 Глубокий анализ (RunPod)", callback_data="route_runpod")
    builder.adjust(1)
    return builder.as_markup()

async def process_album_after_delay(chat_id: int, user_id: int, state: FSMContext, bot: Bot):
    await asyncio.sleep(5.0)
    data = await state.get_data()
    images = data.get("images", [])
    if not images:
        return
    
    # Transition to waiting for route, but with batch data
    await state.set_state(AnalysisSession.waiting_for_route)
    
    await bot.send_message(
        chat_id=chat_id,
        text=f"Получено {len(images)} снимков (Серия). Выберите маршрут обработки:",
        reply_markup=get_batch_keyboard()
    )
    
    # Cleanup task reference
    if user_id in album_tasks:
        del album_tasks[user_id]

@router.message(F.photo)
async def handle_compressed_photo(message: types.Message):
    """
    Handles compressed photos and instructs the user to send them as uncompressed files.
    """
    if not auth_service.is_user_whitelisted(message.from_user.id):
        await message.answer("You are not authorized to use this bot.")
        return
    
    await message.answer(
        "Пожалуйста, отправляйте изображения как 'Файл', а не 'Фото', чтобы избежать сжатия Telegram."
    )

@router.message(F.document)
async def handle_document(message: types.Message, state: FSMContext, bot: Bot):
    """
    Handles documents, distinguishing between uncompressed images (which are processed)
    and other unsupported document types.
    """
    if not auth_service.is_user_whitelisted(message.from_user.id):
        await message.answer("You are not authorized to use this bot.")
        return

    if message.document.mime_type and message.document.mime_type.startswith('image/'):
        # This is an uncompressed image sent as a file, which is what we want.
        # We can treat it like a single image submission.
        await state.clear()
        await state.update_data(
            images=[message.document.file_id],
            file_id=message.document.file_id,
            caption=message.caption or ""
        )
        await state.set_state(AnalysisSession.waiting_for_route)
        await message.answer(
            "Снимок (без сжатия) получен. Выберите маршрут анализа:",
            reply_markup=get_single_image_keyboard()
        )
    else:
        await message.answer("Формат документа не поддерживается. Пожалуйста, отправьте изображение (JPEG/PNG) как 'Файл'.")

