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
    request_timeout: float = 300.0
    
    # Llama.cpp Inference Settings
    llama_model_filename: str = "medgemma-1.5-4b.gguf"
    llama_clip_filename: str = "mmproj-model-f16.gguf"
    # n_gpu_layers: -1 loads all layers to GPU. Reduce this (e.g., 24) if you encounter CUDA Out Of Memory errors.
    llama_n_gpu_layers: int = -1 
    # n_ctx: 2048 is usually enough for a medical image and a short diagnosis. 
    # Reduce (e.g., 1024 or 512) to save VRAM on smaller GPUs like GTX 1060.
    llama_n_ctx: int = 2048
    # Number of CPU threads to use during generation. Optional.
    llama_n_threads: Optional[int] = None
    
    # Pydantic will automatically parse a JSON string from the .env file into a list.
    inference_worker_urls: List[str] = Field(default=[], alias='INFERENCE_WORKER_URLS')

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