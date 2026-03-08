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

@router.message(F.photo & ~F.media_group_id)
async def handle_single_image(message: types.Message, state: FSMContext):
    if not auth_service.is_user_whitelisted(message.from_user.id):
        await message.answer("You are not authorized to use this bot.")
        return

    # Clear any previous state
    await state.clear()

    # Save photo and caption to FSM
    photo = message.photo[-1]
    await state.update_data(
        images=[photo.file_id], # Use a list to unify with batch later if needed, but keep file_id for compatibility
        file_id=photo.file_id,
        caption=message.caption or ""
    )
    await state.set_state(AnalysisSession.waiting_for_route)
    
    await message.answer(
        "Снимок получен. Выберите маршрут анализа:",
        reply_markup=get_single_image_keyboard()
    )

@router.message(F.photo & F.media_group_id)
async def handle_album_image(message: types.Message, state: FSMContext):
    if not auth_service.is_user_whitelisted(message.from_user.id):
        return

    current_state = await state.get_state()
    data = await state.get_data()
    
    # Check if we are already collecting a batch
    if current_state != AnalysisSession.waiting_for_batch_images.state:
        await state.clear()
        await state.set_state(AnalysisSession.waiting_for_batch_images)
        data = {"images": [], "caption": ""}
        
    images = data.get("images", [])
    
    if len(images) >= 20:
        # Prevent spamming the limit warning, just ignore silently or send once
        if len(images) == 20:
            await message.answer("Внимание: достигнут лимит в 20 изображений на пакет. Остальные снимки будут проигнорированы.")
            # Still update state to prevent message from repeating, by making it 21
            images.append("ignored")
            await state.update_data(images=images)
        return
    elif len(images) > 20:
        return

    photo = message.photo[-1]
    images.append(photo.file_id)
    
    caption = data.get("caption", "")
    if message.caption:
        caption = (caption + "\n" + message.caption).strip()

    await state.update_data(images=images, caption=caption)

    user_id = message.from_user.id
    if user_id in album_tasks:
        album_tasks[user_id].cancel()
        
    album_tasks[user_id] = asyncio.create_task(
        process_album_after_delay(message.chat.id, user_id, state, message.bot)
    )

@router.message(F.document)
async def handle_document_fallback(message: types.Message):
    if not auth_service.is_user_whitelisted(message.from_user.id):
        return
    # Check if it's an uncompressed image
    if message.document.mime_type and message.document.mime_type.startswith('image/'):
        await message.answer("Пожалуйста, отправляйте снимки как Фото, а не как Файл (без сжатия).")
    else:
        await message.answer("Формат документа не поддерживается. Отправьте изображение (JPEG/PNG).")

