import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

class GDriveWhitelistService:
    def __init__(self, credentials_json: str | None, file_id: str | None):
        self.credentials_json = credentials_json
        self.file_id = file_id

    def get_whitelist(self) -> list[int]:
        if not self.credentials_json or not self.file_id:
            logger.warning("Google Drive credentials or file_id not configured. Returning empty whitelist.")
            return []
            
        try:
            creds_dict = json.loads(self.credentials_json)
            credentials = Credentials.from_service_account_info(
                creds_dict, scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            service = build('drive', 'v3', credentials=credentials)
            
            request = service.files().get_media(fileId=self.file_id)
            file_content = request.execute()
            
            content_str = file_content.decode('utf-8')
            whitelist = []
            for line in content_str.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Take the first part of the line, splitting by whitespace, to allow for comments
                user_id_str = line.split()[0]
                if user_id_str.isdigit():
                    whitelist.append(int(user_id_str))
            return whitelist
        except Exception as e:
            logger.error(f"Failed to fetch whitelist from Google Drive: {e}")
            return []
