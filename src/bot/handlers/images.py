from aiogram import Router, types, F
from src.bot.services.auth import auth_service
from src.bot.services.api_client import api_client
from io import BytesIO

router = Router()

@router.message(F.photo)
async def handle_image_message(message: types.Message):
    if not auth_service.is_user_whitelisted(message.from_user.id):
        await message.answer("You are not authorized to use this bot.")
        return

    # Indicate processing
    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")
    
    # Download the largest photo size
    photo = message.photo[-1]
    
    # Download into memory (BytesIO) as mandated by Constitution (Principle I: no cloud storage)
    file_in_memory = BytesIO()
    await message.bot.download(photo, destination=file_in_memory)
    image_bytes = file_in_memory.getvalue()
    
    # Forward to local API
    # Optional: include caption if present
    response = await api_client.send_message(
        message.from_user.id, 
        text=message.caption, 
        image_bytes=image_bytes
    )
    
    await message.answer(response)
