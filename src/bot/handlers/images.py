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

async def get_dynamic_keyboard():
    """Fetches available routes from the API and builds a keyboard."""
    try:
        routes_data = await api_client.get_routes()
        routes = routes_data.get("routes", [])
        
        builder = InlineKeyboardBuilder()
        for route in routes:
            builder.button(text=route["name"], callback_data=f"route_{route['id']}")
            
        builder.adjust(1)
        return builder.as_markup()
    except Exception as e:
        # Fallback in case the API is unreachable
        builder = InlineKeyboardBuilder()
        builder.button(text="⚡️ Local (Fallback)", callback_data="route_local_python")
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
    
    keyboard = await get_dynamic_keyboard()
    
    await bot.send_message(
        chat_id=chat_id,
        text=f"Received {len(images)} images (Batch). Please select a processing route:",
        reply_markup=keyboard
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
        "Please send images as 'File' rather than 'Photo' to avoid Telegram compression."
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
        
        keyboard = await get_dynamic_keyboard()
        
        await message.answer(
            "Image received (uncompressed). Please select an analysis route:",
            reply_markup=keyboard
        )
    else:
        await message.answer("Document format not supported. Please send an image (JPEG/PNG) as a 'File'.")

