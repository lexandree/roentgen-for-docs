from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    telegram_id: int
    name: str | None = None
    is_active: bool = True
    system_prompt_type: int = 1
    role: str = "user"
    allowed_workers: list[str] = []
    daily_limit: int = 10
    specialty: str | None = None
    created_at: datetime

class SystemPrompt(BaseModel):
    id: int
    description: str | None = None
    content: str

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

class InteractionLog(BaseModel):
    id: Optional[int] = None
    telegram_id: int
    route: str
    task_type: str
    images_count: int
    status: str
    latency: Optional[float] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    created_at: datetime = datetime.now()
    completed_at: Optional[datetime] = None

