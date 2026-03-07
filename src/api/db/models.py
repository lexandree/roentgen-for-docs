from datetime import datetime
from pydantic import BaseModel

class User(BaseModel):
    telegram_id: int
    name: str | None = None
    is_active: bool = True
    created_at: datetime

class SessionContext(BaseModel):
    session_id: str
    telegram_id: int
    last_activity: datetime
    has_active_image: bool = False

class MessageHistory(BaseModel):
    message_id: int | None = None
    session_id: str
    role: str
    content: str
    timestamp: datetime
