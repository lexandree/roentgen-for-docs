import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import logging
import io

logger = logging.getLogger(__name__)

class GDriveStorageService:
    def __init__(self, credentials_json: str | None, root_folder_id: str | None):
        self.credentials_json = credentials_json
        self.root_folder_id = root_folder_id

    def _get_service(self):
        if not self.credentials_json or not self.root_folder_id:
            raise ValueError("Google Drive credentials or root_folder_id not configured.")
            
        creds_dict = json.loads(self.credentials_json)
        credentials = Credentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/drive']
        )
        return build('drive', 'v3', credentials=credentials)

    def _get_or_create_user_folder(self, service, telegram_id: int) -> str:
        folder_name = str(telegram_id)
        
        # Search for existing folder
        query = f"name='{folder_name}' and '{self.root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        
        if items:
            return items[0]['id']
            
        # Create new folder
        folder_metadata = {
            'name': folder_name,
            'parents': [self.root_folder_id],
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')

    def upload_batch(self, telegram_id: int, files_data: list[tuple[str, bytes, str]]) -> list[str]:
        """
        files_data: list of tuples (filename, content_bytes, mime_type)
        Returns list of uploaded file IDs
        """
        if not self.credentials_json or not self.root_folder_id:
            logger.warning("Google Drive storage is not configured. Skipping upload.")
            return []
            
        try:
            service = self._get_service()
            folder_id = self._get_or_create_user_folder(service, telegram_id)
            
            uploaded_ids = []
            for filename, content, mime_type in files_data:
                file_metadata = {
                    'name': filename,
                    'parents': [folder_id]
                }
                media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mime_type, resumable=True)
                
                file = service.files().create(
                    body=file_metadata, media_body=media, fields='id'
                ).execute()
                uploaded_ids.append(file.get('id'))
                
            return uploaded_ids
        except Exception as e:
            logger.error(f"Failed to upload batch to Google Drive: {e}")
            raise e

    def delete_user_folder(self, telegram_id: int) -> bool:
        if not self.credentials_json or not self.root_folder_id:
            return False
            
        try:
            service = self._get_service()
            folder_name = str(telegram_id)
            
            query = f"name='{folder_name}' and '{self.root_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = service.files().list(q=query, spaces='drive', fields='files(id)').execute()
            items = results.get('files', [])
            
            if items:
                for item in items:
                    service.files().delete(fileId=item['id']).execute()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete user folder from Google Drive: {e}")
            return False
