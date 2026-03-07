import uuid
import os
from datetime import datetime, timezone
from src.api.db.database import get_db

class ChatManager:
    async def get_or_create_session(self, telegram_id: int, db) -> str:
        cursor = await db.execute("SELECT session_id, last_activity FROM session_contexts WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        
        now = datetime.now(timezone.utc)
        if row:
            # Check 24 hour expiry
            last_activity = row["last_activity"]
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity)
            
            if (now - last_activity).total_seconds() > 24 * 3600:
                await self.clear_session(telegram_id, db)
            else:
                await db.execute("UPDATE session_contexts SET last_activity = ? WHERE session_id = ?", (now, row["session_id"]))
                await db.commit()
                return row["session_id"]
                
        # Create new session
        session_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO session_contexts (session_id, telegram_id, last_activity, has_active_image) VALUES (?, ?, ?, 0)",
            (session_id, telegram_id, now)
        )
        await db.commit()
        return session_id

    async def add_message(self, session_id: str, role: str, content: str, db):
        await db.execute(
            "INSERT INTO message_history (session_id, role, content) VALUES (?, ?, ?)",
            (session_id, role, content)
        )
        await db.commit()

    async def get_history(self, session_id: str, db) -> list:
        cursor = await db.execute("SELECT role, content FROM message_history WHERE session_id = ? ORDER BY timestamp ASC", (session_id,))
        rows = await cursor.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    async def save_temp_image(self, session_id: str, file_content: bytes) -> str:
        temp_dir = "temp_images"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        image_path = os.path.join(temp_dir, f"{session_id}_{uuid.uuid4()}.jpg")
        with open(image_path, "wb") as f:
            f.write(file_content)
        return image_path

    async def set_active_image(self, session_id: str, has_active: bool, db):
        await db.execute("UPDATE session_contexts SET has_active_image = ? WHERE session_id = ?", (int(has_active), session_id))
        await db.commit()

    async def clear_session(self, telegram_id: int, db):
        cursor = await db.execute("SELECT session_id FROM session_contexts WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        if row:
            session_id = row["session_id"]
            # Cascade delete in SQLite takes care of history
            await db.execute("DELETE FROM session_contexts WHERE session_id = ?", (session_id,))
            await db.commit()
            # In a real system, we'd also tell the model to drop the KV-cache for this session

chat_manager = ChatManager()
