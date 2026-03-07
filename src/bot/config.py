from pydantic_settings import BaseSettings

class BotSettings(BaseSettings):
    telegram_bot_token: str = ""
    local_api_url: str = "http://127.0.0.1:8000/api/v1"
    google_drive_credentials_json: str | None = None
    whitelist_file_id: str | None = None
    request_timeout: float = 300.0  # Default to 5 minutes for slow local inference

    class Config:
        env_file = ".env"

settings = BotSettings()