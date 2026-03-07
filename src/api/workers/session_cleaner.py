import logging
import asyncio
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.api.db.database import get_db

logger = logging.getLogger(__name__)

class SessionCleaner:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def cleanup_expired_sessions(self):
        logger.info("Running session cleanup worker...")
        async for db in get_db():
            now = datetime.now(timezone.utc)
            expiry_threshold = now - timedelta(hours=24)
            
            # Delete sessions older than 24 hours
            # Cascade delete should take care of history
            await db.execute("DELETE FROM session_contexts WHERE last_activity < ?", (expiry_threshold,))
            await db.commit()
            logger.info("Session cleanup completed.")
            break

    def start(self):
        self.scheduler.add_job(self.cleanup_expired_sessions, 'interval', minutes=60)
        self.scheduler.start()
        logger.info("Session cleanup worker started (runs every 60 minutes).")

session_cleaner = SessionCleaner()
