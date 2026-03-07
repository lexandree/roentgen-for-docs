from pydantic_settings import BaseSettings

class APISettings(BaseSettings):
    google_drive_credentials_json: str | None = None
    whitelist_file_id: str | None = None
    db_path: str = "sqlite+aiosqlite:///local_data.db"
    
    class Config:
        env_file = ".env"

settings = APISettings()