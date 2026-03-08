from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator, Field
import json
import os
from typing import Optional, List

class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

    google_drive_credentials_json: Optional[str] = None
    google_drive_credentials_file_path: Optional[str] = "gdrive_credentials.json"
    whitelist_file_id: Optional[str] = None
    gdrive_batch_folder_id: Optional[str] = None
    db_path: str = "sqlite+aiosqlite:///local_data.db"
    
    # List of worker URLs, comma-separated in the .env file
    inference_worker_urls: List[str] = Field(default=["http://127.0.0.1:8001"])

    @model_validator(mode='before')
    @classmethod
    def split_worker_urls(cls, values):
        """Allow comma-separated string for worker URLs in the env file."""
        worker_urls = values.get('inference_worker_urls')
        if worker_urls and isinstance(worker_urls, str):
            values['inference_worker_urls'] = [url.strip() for url in worker_urls.split(',')]
        return values

    @model_validator(mode='after')
    def load_gdrive_credentials(self) -> 'APISettings':
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

settings = APISettings()