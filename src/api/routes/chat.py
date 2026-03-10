from fastapi import APIRouter, Form, Depends, HTTPException, File, UploadFile
from typing import Annotated, List, Dict
import aiosqlite
import json
import base64
from src.api.db.database import get_db
from src.api.services.auth import auth_service
from src.api.services.chat_manager import chat_manager
from src.api.config import settings
from src.shared.services.gdrive_storage import GDriveStorageService

router = APIRouter(prefix="/api/v1/chat")

@router.get("/routes")
async def get_routes():
    """
    Returns available inference routes configured in the environment.
    Used by the Telegram Bot to dynamically generate the selection menu.
    """
    # Expose only the route_id and human-readable name, NOT the internal URLs
    routes = [{"id": r_id, "name": r_data.get("name", r_id)} for r_id, r_data in settings.inference_workers.items()]
    return {"status": "success", "data": {"routes": routes}}

@router.post("/message")
async def process_message(
    telegram_id: Annotated[int, Form()],
    text: Annotated[str | None, Form()] = None,
    image: Annotated[UploadFile | None, File()] = None,
    route: Annotated[str | None, Form()] = "local_python",
    db: aiosqlite.Connection = Depends(get_db)
):
    user_config = await auth_service.get_user_config(telegram_id, db)
    if not user_config or not user_config.get("is_active"):
        raise HTTPException(status_code=401, detail="User not in whitelist.")

    allowed_workers = json.loads(user_config.get("allowed_workers", "[]"))
    if allowed_workers and route not in allowed_workers:
        raise HTTPException(status_code=403, detail=f"User not permitted to use worker: {route}")

    if not text and not image:
        raise HTTPException(status_code=400, detail="Must provide text or image.")
        
    if route not in settings.inference_workers:
        raise HTTPException(status_code=400, detail=f"Invalid route: {route}")

    log_id = await chat_manager.create_interaction_log(
        telegram_id=telegram_id,
        route=route,
        task_type="single",
        images_count=1 if image else 0,
        db=db
    )

    try:
        # If a new image is uploaded, we assume it's a new patient/case
        # and automatically clear the old session to prevent context overflow.
        if image:
            await chat_manager.clear_session(telegram_id, db)
            
        session_id = await chat_manager.get_or_create_session(telegram_id, db)
        await chat_manager.update_interaction_log(log_id, "processing", db)

        # 1. Build current user message content
        current_content = []
        if image:
            if image.content_type not in ["image/jpeg", "image/png"]:
                raise HTTPException(status_code=400, detail="Only JPEG/PNG supported.")
            file_content = await image.read()
            image_b64 = base64.b64encode(file_content).decode('utf-8')
            current_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}})
            await chat_manager.set_active_image(session_id, True, db)
        
        if text:
            current_content.append({"type": "text", "text": text})
        elif not image:
            current_content.append({"type": "text", "text": "Please continue."})

        # Save current user message to DB as JSON string
        await chat_manager.add_message(session_id, "user", json.dumps(current_content), db)

        # 2. Retrieve history and construct messages array
        full_history = await chat_manager.get_history(session_id, db)
        
        # Trim history to save context, BUT always keep the first message (which contains the image)
        # to ensure the multimodal projector always sees the image and KV cache works.
        if len(full_history) > 6:
            trimmed_history = [full_history[0]] + full_history[-5:]
        else:
            trimmed_history = full_history

        messages = []
        for msg in trimmed_history:
            try:
                # We store complex structures as JSON in DB now
                parsed_content = json.loads(msg["content"])
            except json.JSONDecodeError:
                # Fallback for older text-only DB entries
                parsed_content = [{"type": "text", "text": msg["content"]}]
            messages.append({"role": msg["role"], "content": parsed_content})

        # Get system prompt configured for user
        system_prompt_type = user_config.get("system_prompt_type", 1)
        system_prompt_text = await auth_service.get_system_prompt(system_prompt_type, db)

        # 3. Dispatch full messages array to worker
        response_text = await chat_manager.dispatch_inference_to_worker(messages, system_prompt_text)

        # 4. Save assistant response to history
        assistant_content = [{"type": "text", "text": response_text}]
        await chat_manager.add_message(session_id, "assistant", json.dumps(assistant_content), db)
        
        final_response = f"[{route.upper()}-WORKER] {response_text}"
        await chat_manager.update_interaction_log(log_id, "completed", db)

        return {
            "status": "success", 
            "data": {
                "response": final_response,
                "log_id": log_id
            }
        }
    except Exception as e:
        await chat_manager.update_interaction_log(log_id, "failed", db)
        # Log the full error for debugging
        print(f"!!! DISPATCHER ERROR in /message: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

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
    user_config = await auth_service.get_user_config(telegram_id, db)
    if not user_config or not user_config.get("is_active"):
        raise HTTPException(status_code=401, detail="User not in whitelist.")

    allowed_workers = json.loads(user_config.get("allowed_workers", "[]"))
    if allowed_workers and route not in allowed_workers:
        raise HTTPException(status_code=403, detail=f"User not permitted to use worker: {route}")

    if not images:
        raise HTTPException(status_code=400, detail="Must provide images for batch processing.")

    if len(images) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 images allowed per batch.")

    if route not in settings.inference_workers:
        raise HTTPException(status_code=400, detail=f"Invalid route: {route}")

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