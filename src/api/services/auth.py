import logging
import json
from src.shared.services.gdrive_whitelist import GDriveWhitelistService
from src.api.config import settings

logger = logging.getLogger(__name__)

class APIAuthService:
    def __init__(self):
        self.gdrive_service = GDriveWhitelistService(
            credentials_json=settings.google_drive_credentials_json,
            file_id=settings.whitelist_file_id
        )

    async def sync_whitelist(self, db):
        logger.info("Syncing whitelist from Google Drive...")
        whitelist_data = self.gdrive_service.get_whitelist_data()
        whitelist = whitelist_data.get("users", {})
        prompts = whitelist_data.get("prompts", {})

        if not whitelist:
            logger.warning("Whitelist is empty or failed to fetch.")
            return
            
        # Update SQLite
        try:
            # Sync users
            await db.execute("UPDATE users SET is_active = 0")
            for tid, config in whitelist.items():
                name = config.get("name")
                system_prompt_type = config.get("system_prompt_type", 1)
                role = config.get("role", "user")
                allowed_workers = json.dumps(config.get("allowed_workers", []))
                daily_limit = config.get("daily_limit", 10)
                specialty = config.get("specialty")
                is_active = 1 if config.get("is_active", True) else 0
                show_thoughts = 1 if config.get("show_thoughts", False) else 0

                # Insert or update to active
                await db.execute("""
                    INSERT INTO users (telegram_id, name, is_active, system_prompt_type, role, allowed_workers, daily_limit, specialty, show_thoughts) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(telegram_id) DO UPDATE SET 
                        name = excluded.name,
                        is_active = excluded.is_active,
                        system_prompt_type = excluded.system_prompt_type,
                        role = excluded.role,
                        allowed_workers = excluded.allowed_workers,
                        daily_limit = excluded.daily_limit,
                        specialty = excluded.specialty,
                        show_thoughts = excluded.show_thoughts
                """, (tid, name, is_active, system_prompt_type, role, allowed_workers, daily_limit, specialty, show_thoughts))
                
            # Sync system prompts
            if prompts:
                # We can choose to clear old prompts or just update existing
                # Let's clear and re-insert to keep it clean and match GDrive exactly
                await db.execute("DELETE FROM system_prompts")
                for prompt_id, config in prompts.items():
                    desc = config.get("description", "")
                    content = config.get("content", "")
                    await db.execute("""
                        INSERT INTO system_prompts (id, description, content) 
                        VALUES (?, ?, ?)
                    """, (prompt_id, desc, content))
            
            await db.commit()
            logger.info(f"Successfully synced {len(whitelist)} users and {len(prompts)} prompts to DB.")
        except Exception as e:
            logger.error(f"Error syncing whitelist to DB: {e}")

    async def is_user_whitelisted(self, telegram_id: int, db) -> bool:
        cursor = await db.execute("SELECT is_active FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        if row and row["is_active"]:
            return True
        return False

    async def get_user_config(self, telegram_id: int, db) -> dict | None:
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

    async def get_system_prompt(self, prompt_id: int, db) -> str:
        cursor = await db.execute("SELECT content FROM system_prompts WHERE id = ?", (prompt_id,))
        row = await cursor.fetchone()
        if row and row["content"]:
            return row["content"]
        # Default prompt if not found
        return "You are an expert radiologist AI assistant. Be highly concise, factual, and direct. Do NOT use disclaimers like 'I am an AI' or 'Consult a doctor'. If you need to reason before answering, ALWAYS wrap your reasoning entirely inside <think>...</think> tags."

auth_service = APIAuthService()

from fastapi import Depends, HTTPException
import aiosqlite
from src.api.db.database import get_db

async def is_admin_user(admin_telegram_id: int, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT role FROM users WHERE telegram_id = ? AND is_active = 1", (admin_telegram_id,))
    row = await cursor.fetchone()
    if not row or row["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return admin_telegram_id
