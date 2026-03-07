import logging
from src.shared.services.gdrive_whitelist import GDriveWhitelistService
from src.bot.config import settings

logger = logging.getLogger(__name__)

class BotAuthService:
    def __init__(self):
        self.gdrive_service = GDriveWhitelistService(
            credentials_json=settings.google_drive_credentials_json,
            file_id=settings.whitelist_file_id
        )
        self.cached_whitelist: set[int] = set()

    def sync_whitelist(self):
        logger.info("Bot syncing whitelist from Google Drive...")
        whitelist = self.gdrive_service.get_whitelist()
        if whitelist:
            self.cached_whitelist = set(whitelist)
            logger.info(f"Bot successfully cached {len(self.cached_whitelist)} users.")
        else:
            logger.warning("Bot whitelist fetch returned empty.")

    def is_user_whitelisted(self, telegram_id: int) -> bool:
        return telegram_id in self.cached_whitelist

auth_service = BotAuthService()
