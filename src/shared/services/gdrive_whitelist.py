import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

class GDriveWhitelistService:
    def __init__(self, credentials_json: str | None, file_id: str | None):
        self.credentials_json = credentials_json
        self.file_id = file_id

    def get_whitelist_data(self) -> dict:
        if not self.credentials_json or not self.file_id:
            logger.warning("Google Drive credentials or file_id not configured. Returning empty data.")
            return {"users": {}, "prompts": {}}
            
        try:
            creds_dict = json.loads(self.credentials_json)
            credentials = Credentials.from_service_account_info(
                creds_dict, scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            service = build('drive', 'v3', credentials=credentials)
            
            request = service.files().get_media(fileId=self.file_id)
            file_content = request.execute()
            
            content_str = file_content.decode('utf-8')
            parsed_data = json.loads(content_str)
            
            # Handle legacy format where root is just users, or new format with users and prompts
            if "users" in parsed_data:
                users_data = parsed_data.get("users", {})
                prompts_data = parsed_data.get("prompts", {})
            else:
                users_data = parsed_data
                prompts_data = {}
            
            whitelist = {}
            for user_id_str, config in users_data.items():
                if user_id_str.isdigit():
                    whitelist[int(user_id_str)] = config
                    
            prompts = {}
            for prompt_id_str, config in prompts_data.items():
                if prompt_id_str.isdigit():
                    prompts[int(prompt_id_str)] = config
                    
            return {"users": whitelist, "prompts": prompts}
        except Exception as e:
            logger.error(f"Failed to fetch whitelist from Google Drive: {e}")
            return {"users": {}, "prompts": {}}

    def get_whitelist(self) -> dict[int, dict]:
        # Legacy compat
        return self.get_whitelist_data().get("users", {})
