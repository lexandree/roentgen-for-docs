import aiosqlite
from src.api.config import settings

async def get_db():
    db_path = settings.db_path.replace("sqlite+aiosqlite:///", "")
    db = await aiosqlite.connect(db_path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

async def init_db():
    db_path = settings.db_path.replace("sqlite+aiosqlite:///", "")
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                name TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS session_contexts (
                session_id TEXT PRIMARY KEY,
                telegram_id INTEGER,
                last_activity TIMESTAMP,
                has_active_image BOOLEAN DEFAULT 0,
                FOREIGN KEY(telegram_id) REFERENCES users(telegram_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS message_history (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES session_contexts(session_id) ON DELETE CASCADE
            )
        """)
        await db.commit()