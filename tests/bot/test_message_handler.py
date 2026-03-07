import pytest
from unittest.mock import AsyncMock, MagicMock
from src.bot.handlers.messages import handle_text_message
from src.bot.handlers.images import handle_image_message
from aiogram import types

@pytest.mark.asyncio
async def test_handle_text_message_unauthorized():
    # Mock message
    message = AsyncMock(spec=types.Message)
    message.from_user.id = 999
    message.text = "Hello"
    message.answer = AsyncMock()
    
    # Mock auth service to return False
    from src.bot.services.auth import auth_service
    auth_service.is_user_whitelisted = MagicMock(return_value=False)
    
    await handle_text_message(message)
    
    message.answer.assert_called_with("You are not authorized to use this bot.")

@pytest.mark.asyncio
async def test_handle_image_message_unauthorized():
    message = AsyncMock(spec=types.Message)
    message.from_user.id = 999
    message.photo = [MagicMock(spec=types.PhotoSize)]
    message.answer = AsyncMock()
    
    from src.bot.services.auth import auth_service
    auth_service.is_user_whitelisted = MagicMock(return_value=False)
    
    await handle_image_message(message)
    
    message.answer.assert_called_with("You are not authorized to use this bot.")
