from fastapi import APIRouter, Depends
import aiosqlite
from src.api.db.database import get_db
from src.api.services.auth import is_admin_user
from src.api.services.chat_manager import chat_manager

router = APIRouter(prefix="/api/v1/admin")

@router.get("/status")
async def get_admin_status(admin_id: int = Depends(is_admin_user)):
    statuses = await chat_manager.ping_workers()
    return {"status": "success", "data": {"workers": statuses}}

@router.get("/stats")
async def get_admin_stats(period: str = "daily", admin_id: int = Depends(is_admin_user), db: aiosqlite.Connection = Depends(get_db)):
    stats = await chat_manager.get_system_stats(db, period)
    return {"status": "success", "data": {"stats": stats}}

@router.get("/user_stats/{telegram_id}")
async def get_admin_user_stats(telegram_id: int, admin_id: int = Depends(is_admin_user), db: aiosqlite.Connection = Depends(get_db)):
    stats = await chat_manager.get_user_stats(db, telegram_id)
    return {"status": "success", "data": {"user_stats": stats}}

@router.get("/worker_stats")
async def get_admin_worker_stats(period: str = "daily", admin_id: int = Depends(is_admin_user), db: aiosqlite.Connection = Depends(get_db)):
    stats = await chat_manager.get_worker_stats(db, period)
    return {"status": "success", "data": {"worker_stats": stats}}
