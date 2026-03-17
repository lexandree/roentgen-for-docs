import logging
import asyncio
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.api.db.database import get_db
from src.api.config import settings

logger = logging.getLogger(__name__)

class SessionCleaner:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def cleanup_expired_sessions(self):
        logger.info("Running session cleanup worker...")
        async for db in get_db():
            now = datetime.now(timezone.utc)
            expiry_threshold = now - timedelta(seconds=settings.session_timeout_seconds)
            
            # Delete sessions older than timeout
            # Cascade delete should take care of history
            await db.execute("DELETE FROM session_contexts WHERE last_activity < ?", (expiry_threshold,))
            await db.commit()
            logger.info("Session cleanup completed.")
            break

    def start(self):
        # Run cleanup more frequently if timeout is short
        interval_minutes = max(1, settings.session_timeout_seconds // 60)
        self.scheduler.add_job(self.cleanup_expired_sessions, 'interval', minutes=interval_minutes)
        self.scheduler.start()
        logger.info(f"Session cleanup worker started (runs every {interval_minutes} minutes).")

session_cleaner = SessionCleaner()
