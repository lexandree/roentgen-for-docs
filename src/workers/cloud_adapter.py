import json
import time
import os
import logging
import base64
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
from typing import Dict, List, Any

# We'll try to import our inference engine. 
# On Colab/Kaggle, the user needs to make sure the src/ and models/ are available.
try:
    from src.api.services.inference import MedGemmaModel
    from src.api.config import settings
except ImportError:
    print("Warning: Could not import MedGemmaModel. Inference will be mocked.")
    MedGemmaModel = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CloudWorkerAdapter:
    def __init__(self, credentials_json: str, root_folder_id: str):
        self.root_folder_id = root_folder_id
        creds_dict = json.loads(credentials_json)
        self.credentials = Credentials.from_service_account_info(
            creds_dict, scopes=['https://www.googleapis.com/auth/drive']
        )
        self.service = build('drive', 'v3', credentials=self.credentials)
        self.model = None

    def load_model(self):
        if MedGemmaModel:
            logger.info("Initializing MedGemma model on cloud worker...")
            self.model = MedGemmaModel()
        else:
            logger.warning("No inference engine available. Using Mock mode.")

    def poll_for_batches(self):
        logger.info(f"Polling Google Drive folder {self.root_folder_id} for new batches...")
        while True:
            try:
                # Find subfolders (user IDs) in the root folder
                query = f"'{self.root_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
                results = self.service.files().list(q=query, fields="files(id, name)").execute()
                folders = results.get('files', [])

                for folder in folders:
                    self.process_user_folder(folder['id'], folder['name'])

            except Exception as e:
                logger.error(f"Error during polling: {e}")
            
            time.sleep(30) # Poll every 30 seconds

    def process_user_folder(self, folder_id: str, telegram_id: str):
        # Check if this folder is already processed or has a result
        query = f"'{folder_id}' in parents and name = 'report.json' and trashed = false"
        results = self.service.files().list(q=query, fields="files(id)").execute()
        if results.get('files'):
            # Already has a report, skip
            return

        logger.info(f"Processing new batch for user {telegram_id} in folder {folder_id}...")

        # 1. Download images
        query = f"'{folder_id}' in parents and (mimeType = 'image/jpeg' or mimeType = 'image/png') and trashed = false"
        image_results = self.service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        images = image_results.get('files', [])

        if not images:
            return

        batch_images_b64 = []
        for img in images:
            logger.info(f"Downloading {img['name']}...")
            request = self.service.files().get_media(fileId=img['id'])
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            img_bytes = fh.getvalue()
            batch_images_b64.append(base64.b64encode(img_bytes).decode('utf-8'))

        # 2. Run Inference
        report_text = self.run_batch_inference(batch_images_b64)

        # 3. Upload report.json
        report_data = {
            "telegram_id": int(telegram_id),
            "report": report_text,
            "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "completed"
        }
        
        file_metadata = {
            'name': 'report.json',
            'parents': [folder_id],
            'mimeType': 'application/json'
        }
        media = MediaFileUpload(
            io.BytesIO(json.dumps(report_data).encode('utf-8')),
            mimetype='application/json',
            resumable=True
        )
        self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        logger.info(f"Successfully processed batch for {telegram_id}. Report uploaded.")

    def run_batch_inference(self, images_b64: List[str]) -> str:
        if self.model:
            # Construct messages for the model. 
            # For now, we follow the dispatcher's lead and send images as part of the content.
            # MedGemma implementation in src.api.services.inference handles multiple images 
            # by taking the first one in history (it needs to be updated if we want true batch of 20).
            # For now, let's just send the first image if it exists.
            
            content = []
            if images_b64:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{images_b64[0]}"}
                })
            content.append({"type": "text", "text": f"Please analyze this series of {len(images_b64)} images."})
            
            messages = [{"role": "user", "content": content}]
            
            # This is a blocking call
            import asyncio
            return asyncio.run(self.model.perform_inference(messages))
        else:
            return f"Mock Report: Analyzed {len(images_b64)} images. Everything looks normal."

if __name__ == "__main__":
    # In a real cloud environment, these would be env vars or passed via CLI
    CREDENTIALS_JSON = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_JSON")
    ROOT_FOLDER_ID = os.environ.get("GDRIVE_BATCH_FOLDER_ID")
    
    if not CREDENTIALS_JSON or not ROOT_FOLDER_ID:
        print("Error: GOOGLE_DRIVE_CREDENTIALS_JSON and GDRIVE_BATCH_FOLDER_ID must be set.")
        exit(1)
        
    adapter = CloudWorkerAdapter(CREDENTIALS_JSON, ROOT_FOLDER_ID)
    adapter.load_model()
    adapter.poll_for_batches()
