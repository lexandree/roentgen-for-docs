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
                system_prompt_type INTEGER DEFAULT 1,
                role TEXT DEFAULT 'user',
                allowed_workers TEXT DEFAULT '[]',
                daily_limit INTEGER DEFAULT 10,
                specialty TEXT,
                show_thoughts BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS system_prompts (
                id INTEGER PRIMARY KEY,
                description TEXT,
                content TEXT NOT NULL
            )
        """)

        # Migrations for users table
        columns_to_add_users = [
            ("system_prompt_type", "INTEGER DEFAULT 1"),
            ("role", "TEXT DEFAULT 'user'"),
            ("allowed_workers", "TEXT DEFAULT '[]'"),
            ("daily_limit", "INTEGER DEFAULT 10"),
            ("specialty", "TEXT"),
            ("show_thoughts", "BOOLEAN DEFAULT 0")
        ]
        for col_name, col_type in columns_to_add_users:
            try:
                await db.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            except aiosqlite.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise e

        await db.execute("""
            CREATE TABLE IF NOT EXISTS session_contexts (
                session_id TEXT PRIMARY KEY,
                telegram_id INTEGER,
                last_activity TIMESTAMP,
                has_active_image BOOLEAN DEFAULT 0,
                current_route TEXT,
                FOREIGN KEY(telegram_id) REFERENCES users(telegram_id)
            )
        """)
        
        # Migrations for session_contexts table
        try:
            await db.execute("ALTER TABLE session_contexts ADD COLUMN current_route TEXT")
        except aiosqlite.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                raise e

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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS interaction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                route TEXT NOT NULL,
                task_type TEXT NOT NULL,
                images_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                latency REAL,
                input_tokens INTEGER,
                output_tokens INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY(telegram_id) REFERENCES users(telegram_id)
            )
        """)

        # Migrations for interaction_logs table
        columns_to_add_logs = [
            ("latency", "REAL"),
            ("input_tokens", "INTEGER"),
            ("output_tokens", "INTEGER")
        ]
        for col_name, col_type in columns_to_add_logs:
            try:
                await db.execute(f"ALTER TABLE interaction_logs ADD COLUMN {col_name} {col_type}")
            except aiosqlite.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise e

        await db.commit()