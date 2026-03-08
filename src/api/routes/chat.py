from fastapi import APIRouter, Form, Depends, HTTPException, File, UploadFile
from typing import Annotated, List
import aiosqlite
from src.api.db.database import get_db
from src.api.services.auth import auth_service
from src.api.services.chat_manager import chat_manager
from src.api.services.inference import inference_service
from src.api.config import settings
from src.shared.services.gdrive_storage import GDriveStorageService

router = APIRouter(prefix="/api/v1/chat")

@router.post("/message")
async def process_message(
    telegram_id: Annotated[int, Form()],
    text: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
    route: Annotated[str | None, Form()] = "local",
    db: aiosqlite.Connection = Depends(get_db)
):
    if not await auth_service.is_user_whitelisted(telegram_id, db):
        raise HTTPException(status_code=401, detail="User not in whitelist.")

    if not text and not image:
        raise HTTPException(status_code=400, detail="Must provide text or image.")

    log_id = await chat_manager.create_interaction_log(
        telegram_id=telegram_id,
        route=route,
        task_type="single",
        images_count=1 if image else 0,
        db=db
    )

    try:
        session_id = await chat_manager.get_or_create_session(telegram_id, db)

        image_path = None
        if image:
            if image.content_type not in ["image/jpeg", "image/png"]:
                raise HTTPException(status_code=400, detail="Only JPEG/PNG supported.")

            file_content = await image.read()
            image_path = await chat_manager.save_temp_image(session_id, file_content)
            await chat_manager.set_active_image(session_id, True, db)

        if text:
            await chat_manager.add_message(session_id, "user", text, db)

        await chat_manager.update_interaction_log(log_id, "processing", db)

        history = await chat_manager.get_history(session_id, db)

        # Inference handles image deletion after vectorization
        response_text = await inference_service.generate_response(text, image_path, history)

        response_text = f"[{route.upper()}] {response_text}"

        await chat_manager.add_message(session_id, "assistant", response_text, db)
        
        await chat_manager.update_interaction_log(log_id, "completed", db)

        return {
            "status": "success", 
            "data": {
                "response": response_text,
                "log_id": log_id
            }
        }
    except Exception as e:
        await chat_manager.update_interaction_log(log_id, "failed", db)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear")
async def clear_chat(data: dict, db: aiosqlite.Connection = Depends(get_db)):
    telegram_id = data.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="telegram_id required.")

    await chat_manager.clear_session(telegram_id, db)
    return {"status": "success", "message": "Session cleared successfully."}

@router.post("/batch")
async def process_batch(
    telegram_id: Annotated[int, Form()],
    route: Annotated[str, Form()],
    text: Annotated[str | None, Form()] = None,
    images: List[UploadFile] = File(...),
    db: aiosqlite.Connection = Depends(get_db)
):
    if not await auth_service.is_user_whitelisted(telegram_id, db):
        raise HTTPException(status_code=401, detail="User not in whitelist.")

    if not images:
        raise HTTPException(status_code=400, detail="Must provide images for batch processing.")

    if len(images) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 images allowed per batch.")

    if route == "local":
        raise HTTPException(status_code=400, detail="Local route does not support batch processing.")

    log_id = await chat_manager.create_interaction_log(
        telegram_id=telegram_id,
        route=route,
        task_type="batch",
        images_count=len(images),
        db=db
    )

    try:
        await chat_manager.update_interaction_log(log_id, "processing", db)
        
        gdrive_service = GDriveStorageService(
            credentials_json=settings.google_drive_credentials_json,
            root_folder_id=settings.gdrive_batch_folder_id
        )

        files_data = []
        for image in images:
            if image.content_type not in ["image/jpeg", "image/png"]:
                raise HTTPException(status_code=400, detail="Only JPEG/PNG supported.")
            content = await image.read()
            files_data.append((image.filename, content, image.content_type))
            
        uploaded_ids = gdrive_service.upload_batch(telegram_id, files_data)
        
        # Batch is successfully queued in GDrive for processing
        await chat_manager.update_interaction_log(log_id, "completed", db)
        
        return {
            "status": "queued",
            "data": {
                "message": f"Batch accepted and routed to {route}.",
                "log_id": log_id,
                "images_count": len(uploaded_ids)
            }
        }
    except Exception as e:
        await chat_manager.update_interaction_log(log_id, "failed", db)
        raise HTTPException(status_code=500, detail=f"Failed to process batch: {e}")

@router.delete("/batch")
async def cancel_batch(data: dict, db: aiosqlite.Connection = Depends(get_db)):
    telegram_id = data.get("telegram_id")
    if not telegram_id:
        raise HTTPException(status_code=400, detail="telegram_id required.")

    if not await auth_service.is_user_whitelisted(telegram_id, db):
        raise HTTPException(status_code=401, detail="User not in whitelist.")

    gdrive_service = GDriveStorageService(
        credentials_json=settings.google_drive_credentials_json,
        root_folder_id=settings.gdrive_batch_folder_id
    )
    
    success = gdrive_service.delete_user_folder(telegram_id)
    if success:
        return {"status": "success", "data": {"message": "Batch cancelled and files cleaned up."}}
    else:
        return {"status": "success", "data": {"message": "No active batch files found or error during cleanup."}}