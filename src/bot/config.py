from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
import os
from typing import Optional

class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    telegram_bot_token: str = ""
    local_api_url: str = "http://127.0.0.1:8000/api/v1"
    google_drive_credentials_json: Optional[str] = None
    google_drive_credentials_file_path: Optional[str] = "gdrive_credentials.json"
    whitelist_file_id: str | None = None
    request_timeout: float = 300.0  # Default to 5 minutes. Override via REQUEST_TIMEOUT in bot.env if needed.

    @model_validator(mode='after')
    def load_gdrive_credentials(self) -> 'BotSettings':
        # Prioritize loading from file if the path is provided and exists
        credentials_file = self.google_drive_credentials_file_path
        if credentials_file and os.path.exists(credentials_file):
            try:
                with open(credentials_file, 'r') as f:
                    self.google_drive_credentials_json = f.read()
            except Exception as e:
                raise ValueError(f"Could not read Google Drive credentials from {credentials_file}: {e}")
        
        # If after all attempts, we have a file_id but no credentials, it's an error.
        if self.whitelist_file_id and not self.google_drive_credentials_json:
            raise ValueError(
                "Whitelist file ID is provided, but no Google Drive credentials could be loaded. "
                "Please set GOOGLE_DRIVE_CREDENTIALS_JSON or provide a valid file path in "
                "GOOGLE_DRIVE_CREDENTIALS_FILE_PATH."
            )
        return self

settings = BotSettings()