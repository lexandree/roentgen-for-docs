from fastapi import APIRouter, Form, Depends, HTTPException, File, UploadFile
from typing import Annotated
import aiosqlite
from src.api.db.database import get_db
from src.api.services.auth import auth_service
from src.api.services.chat_manager import chat_manager
from src.api.services.inference import inference_service

router = APIRouter(prefix="/api/v1/chat")

@router.post("/message")
async def process_message(
    telegram_id: Annotated[int, Form()],
    text: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
    db: aiosqlite.Connection = Depends(get_db)
):
    if not await auth_service.is_user_whitelisted(telegram_id, db):
        raise HTTPException(status_code=401, detail="User not in whitelist.")
        
    if not text and not image:
        raise HTTPException(status_code=400, detail="Must provide text or image.")

    session_id = await chat_manager.get_or_create_session(telegram_id, db)
    
    image_path = None
    if image:
        # Validate format
        if image.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(status_code=400, detail="Only JPEG/PNG supported.")
        
        file_content = await image.read()
        image_path = await chat_manager.save_temp_image(session_id, file_content)
        await chat_manager.set_active_image(session_id, True, db)

    if text:
        await chat_manager.add_message(session_id, "user", text, db)
        
    history = await chat_manager.get_history(session_id, db)
    
    # Inference handles image deletion after vectorization
    response_text = await inference_service.generate_response(text, image_path, history)
    
    await chat_manager.add_message(session_id, "assistant", response_text, db)
    
    return {"status": "success", "response": response_text}

@router.post("/clear")
async def clear_chat(data: dict, db: aiosqlite.Connection = Depends(get_db)):
    telegram_id = data.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="telegram_id required.")
    
    await chat_manager.clear_session(telegram_id, db)
    return {"status": "success", "message": "Session cleared successfully."}