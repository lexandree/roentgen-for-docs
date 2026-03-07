from aiogram import Router, types
from aiogram.filters import Command
from src.bot.services.auth import auth_service
from src.bot.services.api_client import api_client

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    if not auth_service.is_user_whitelisted(message.from_user.id):
        await message.answer("You are not authorized to use this bot.")
        return
    await message.answer("Welcome to MedGemma Diagnostic Bot. You can send me a text query or upload an X-ray/MRI image for analysis.")

@router.message(Command("clear"))
async def cmd_clear(message: types.Message):
    if not auth_service.is_user_whitelisted(message.from_user.id):
        return
    success = await api_client.clear_session(message.from_user.id)
    if success:
        await message.answer("Conversation context and active image have been cleared.")
    else:
        await message.answer("Failed to clear session on the server.")

@router.message(Command("refresh_whitelist"))
async def cmd_refresh_whitelist(message: types.Message):
    # In a real scenario, you might restrict this to admins
    auth_service.sync_whitelist()
    await message.answer("Whitelist has been refreshed from Google Drive.")

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
