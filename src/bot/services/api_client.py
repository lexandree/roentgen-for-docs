import httpx
import logging
from src.bot.config import settings

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        self.base_url = settings.local_api_url
        self.timeout = settings.request_timeout

    async def send_message(self, telegram_id: int, text: str | None = None, image_bytes: bytes | None = None) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            data = {"telegram_id": telegram_id}
            if text:
                data["text"] = text
            
            files = {}
            if image_bytes:
                files = {"image": ("image.jpg", image_bytes, "image/jpeg")}

            try:
                response = await client.post(f"{self.base_url}/chat/message", data=data, files=files)
                response.raise_for_status()
                result = response.json()
                return result.get("response", "No response from AI.")
            except httpx.TimeoutException:
                logger.error("Timeout connecting to local API")
                return "The local MedGemma server is taking too long to respond. Please try again later."
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return "You are not authorized to use this bot."
                logger.error(f"HTTP error from local API: {e}")
                return "An error occurred while communicating with the diagnostic server."
            except Exception as e:
                logger.error(f"Unexpected error connecting to local API: {e}")
                return "The local diagnostic server is currently unreachable."

    async def clear_session(self, telegram_id: int) -> bool:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(f"{self.base_url}/chat/clear", json={"telegram_id": telegram_id})
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Error clearing session: {e}")
                return False

api_client = APIClient()
