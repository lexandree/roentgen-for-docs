from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from src.bot.services.auth import auth_service
from src.bot.services.api_client import api_client
from src.bot.states import AnalysisSession
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio
from typing import Dict

router = Router()

media_groups: Dict[str, dict] = {}

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

def get_roi_keyboard():
    """Builds a keyboard for Region of Interest (ROI) selection."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Analyze Full Image", callback_data="roi_none")
    builder.button(text="↖️ Top Left", callback_data="roi_top_left")
    builder.button(text="↗️ Top Right", callback_data="roi_top_right")
    builder.button(text="⏺ Center", callback_data="roi_center")
    builder.button(text="↙️ Bottom Left", callback_data="roi_bottom_left")
    builder.button(text="↘️ Bottom Right", callback_data="roi_bottom_right")
    # Adjust layout: 1 full width, then 2 buttons per row, then 2 buttons
    builder.adjust(1, 2, 1, 2)
    return builder.as_markup()

async def process_album_after_delay(group_id: str, bot: Bot):
    await asyncio.sleep(3.0)
    if group_id not in media_groups:
        return
        
    group_data = media_groups.pop(group_id)
    state: FSMContext = group_data["state"]
    chat_id = group_data["chat_id"]
    images = group_data["images"]
    caption = group_data["caption"]
    
    if not images:
        return
        
    await state.clear()
    await state.update_data(
        images=images,
        caption=caption,
        is_batch_upload=False
    )
    await state.set_state(AnalysisSession.waiting_for_route)
    
    keyboard = await get_dynamic_keyboard()
    await bot.send_message(
        chat_id=chat_id,
        text=f"Received {len(images)} images (Album). Please select a processing route:",
        reply_markup=keyboard
    )

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
    and other unsupported document types. Supports grouping (albums).
    """
    if not auth_service.is_user_whitelisted(message.from_user.id):
        await message.answer("You are not authorized to use this bot.")
        return

    if message.document.mime_type and message.document.mime_type.startswith('image/'):
        if message.media_group_id:
            group_id = message.media_group_id
            if group_id not in media_groups:
                media_groups[group_id] = {
                    "images": [],
                    "caption": message.caption or "",
                    "chat_id": message.chat.id,
                    "user_id": message.from_user.id,
                    "state": state
                }
                await state.set_state(AnalysisSession.collecting_album)
                await state.update_data(current_media_group_id=group_id)
                asyncio.create_task(process_album_after_delay(group_id, bot))
            
            media_groups[group_id]["images"].append({
                "msg_id": message.message_id, 
                "file_id": message.document.file_id,
                "file_name": message.document.file_name
            })
            
            if not media_groups[group_id]["caption"] and message.caption:
                media_groups[group_id]["caption"] = message.caption
                
            return
        else:
            # Single image submission
            await state.clear()
            await state.update_data(
                images=[{
                    "msg_id": message.message_id, 
                    "file_id": message.document.file_id,
                    "file_name": message.document.file_name
                }],
                caption=message.caption or "",
                is_batch_upload=False
            )
            await state.set_state(AnalysisSession.waiting_for_roi)
            
            keyboard = get_roi_keyboard()
            await message.answer(
                "Image received (uncompressed). Select an area to focus on, or analyze the full image:",
                reply_markup=keyboard
            )
    else:
        await message.answer("Document format not supported. Please send an image (JPEG/PNG) as a 'File'.")

