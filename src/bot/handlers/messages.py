from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from src.bot.services.auth import auth_service
from src.bot.services.api_client import api_client
from src.bot.states import AnalysisSession
from io import BytesIO

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if not auth_service.is_user_whitelisted(message.from_user.id):
        await message.answer("You are not authorized to use this bot.")
        return
    await message.answer("Welcome to MedGemma Diagnostic Bot. You can send me a text query or upload an X-ray/MRI image for analysis.")

@router.message(Command("status"))
async def cmd_status(message: types.Message):
    if not auth_service.is_user_whitelisted(message.from_user.id):
        return
    
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    statuses = await api_client.get_workers_status()
    session_info = await api_client.get_session_info(message.from_user.id)
    
    if not statuses:
        await message.answer("⚠️ Failed to retrieve server statuses. Dispatcher might be offline.")
        return
        
    response_lines = ["*Inference Servers Status:*"]
    for route_id, info in statuses.items():
        name = info.get("name", route_id)
        status = info.get("status", "unknown")
        
        # Highlight active route
        is_active = session_info.get("active_session") and session_info.get("route") == route_id
        active_marker = " (👈 Current)" if is_active else ""
        
        if status == "online":
            icon = "🟢"
            status_text = "Online"
        elif status == "serverless":
            icon = "☁️"
            status_text = f"Serverless ({info.get('reason', 'Wakes up on request')})"
        elif "timeout" in status:
            icon = "🟡"
            status_text = "Standby (Waiting)"
        else:
            icon = "🔴"
            status_text = f"Offline ({status})"
            
        response_lines.append(f"{icon} *{name}*: {status_text}{active_marker}")
        
    if session_info.get("active_session") and session_info.get("has_image"):
        response_lines.append("\n🖼 *Active image in memory.*")
        
    await message.answer("\n".join(response_lines), parse_mode="Markdown")

@router.message(Command("model"))
async def cmd_model(message: types.Message, state: FSMContext):
    if not auth_service.is_user_whitelisted(message.from_user.id):
        return
    from src.bot.handlers.images import get_dynamic_keyboard
    
    # Store that we are just changing route without an image
    await state.set_state(AnalysisSession.waiting_for_route)
    await state.update_data(images=[], caption="", file_id=None, is_text_only_route_switch=True)
    
    keyboard = await get_dynamic_keyboard()
    await message.answer("Select an inference worker for the current conversation:", reply_markup=keyboard)

@router.message(Command("analyze"))
async def cmd_analyze(message: types.Message, state: FSMContext):
    if not auth_service.is_user_whitelisted(message.from_user.id):
        return
    await state.clear()
    await state.set_state(AnalysisSession.waiting_for_batch_images)
    await state.update_data(images=[], caption="")
    await message.answer("Batch upload mode activated. Send a series of images (one by one or as an album).")

@router.message(Command("clear"))
async def cmd_clear(message: types.Message, state: FSMContext):
    if not auth_service.is_user_whitelisted(message.from_user.id):
        return

    current_state = await state.get_state()
    if current_state:
        await state.clear()

    # Always call both clears just to be safe
    success_session = await api_client.clear_session(message.from_user.id)
    success_batch = await api_client.cancel_batch(message.from_user.id)

    if success_session or success_batch:
        await message.answer("Conversation context and pending batches have been cleared.")
    else:
        await message.answer("Cleared local state, but encountered an issue clearing remote server state.")

@router.message(Command("end"))
async def cmd_end(message: types.Message, state: FSMContext):
    """
    Explicitly end the conversation session.
    Same logic as /clear but with a more 'user-friendly' semantic meaning for doctors.
    """
    if not auth_service.is_user_whitelisted(message.from_user.id):
        return

    await state.clear()
    await api_client.clear_session(message.from_user.id)
    await message.answer("Session ended. History cleared. You can start a new analysis.")
@router.message(Command("refresh_whitelist"))
async def cmd_refresh_whitelist(message: types.Message):
    user = auth_service.get_user(message.from_user.id)
    if not user or user.get("role") != "admin":
        await message.answer("You are not authorized to use this command.")
        return
        
    auth_service.sync_whitelist()
    await message.answer("Whitelist has been refreshed from Google Drive.")

@router.callback_query(AnalysisSession.waiting_for_route, F.data.startswith("route_"))
async def process_route_selection(callback: types.CallbackQuery, state: FSMContext):
    if not auth_service.is_user_whitelisted(callback.from_user.id):
        await callback.answer("Unauthorized", show_alert=True)
        return

    route = callback.data.replace("route_", "")
    data = await state.get_data()
    file_id = data.get("file_id")
    images = data.get("images", [])
    caption = data.get("caption")
    is_text_only = data.get("is_text_only_route_switch", False)
    is_batch_upload = data.get("is_batch_upload", True) # Default True for legacy compatibility

    await state.clear()
    
    if is_text_only:
        success = await api_client.set_session_route(callback.from_user.id, route)
        if success:
            await callback.message.edit_text(f"✅ Worker for current conversation changed to: {route.upper()}")
        else:
            await callback.message.edit_text("❌ Error changing worker.")
        await callback.answer()
        return

    await callback.message.edit_text(f"Route selected: {route.upper()}. Starting upload...")
    await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action="upload_photo")

    try:
        # Determine if this is a cloud batch or local multi-image request
        if is_batch_upload and (len(images) > 1 or (not file_id and images)):
            # Cloud Batch processing
            images_bytes = []
            for img_id in images:
                if img_id == "ignored":
                    continue
                file_in_memory = BytesIO()
                await callback.bot.download(img_id, destination=file_in_memory)
                images_bytes.append(file_in_memory.getvalue())
                
            response = await api_client.send_batch(
                callback.from_user.id,
                images_bytes=images_bytes,
                route=route,
                text=caption
            )
        else:
            # Local processing (Single or Multi-image Album)
            images_bytes = []
            if images:
                for img_id in images:
                    if img_id == "ignored":
                        continue
                    file_in_memory = BytesIO()
                    await callback.bot.download(img_id, destination=file_in_memory)
                    images_bytes.append(file_in_memory.getvalue())

            response = await api_client.send_message(
                callback.from_user.id, 
                text=caption, 
                images_bytes=images_bytes,
                route=route
            )
        
        await callback.message.answer(response)
    except Exception as e:
        await callback.message.answer(f"Failed to download/process images: {e}")
    finally:
        await callback.answer()

@router.message()
async def handle_unsupported_message(message: types.Message):
    if not auth_service.is_user_whitelisted(message.from_user.id):
        return
        
    if message.text:
        # Handle text as normal
        # Indicate processing
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        response = await api_client.send_message(message.from_user.id, text=message.text)
        await message.answer(response)
    else:
        # Unsupported format (document, video, etc)
        await message.answer("Unsupported file format. Please upload an X-ray or MRI image (JPEG/PNG) or send a text query.")

