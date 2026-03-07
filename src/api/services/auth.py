import logging
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
        whitelist = self.gdrive_service.get_whitelist()
        if not whitelist:
            logger.warning("Whitelist is empty or failed to fetch.")
            return
            
        # Update SQLite
        try:
            # Set all to inactive first
            await db.execute("UPDATE users SET is_active = 0")
            for tid in whitelist:
                # Insert or update to active
                await db.execute("""
                    INSERT INTO users (telegram_id, is_active) 
                    VALUES (?, 1)
                    ON CONFLICT(telegram_id) DO UPDATE SET is_active = 1
                """, (tid,))
            await db.commit()
            logger.info(f"Successfully synced {len(whitelist)} users to whitelist.")
        except Exception as e:
            logger.error(f"Error syncing whitelist to DB: {e}")

    async def is_user_whitelisted(self, telegram_id: int, db) -> bool:
        cursor = await db.execute("SELECT is_active FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        if row and row["is_active"]:
            return True
        return False

auth_service = APIAuthService()
