import httpx
import logging
from src.bot.config import settings

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        self.base_url = settings.local_api_url
        self.timeout = settings.request_timeout

    async def get_routes(self) -> dict:
        """Fetches the available inference routes from the Dispatcher API."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.base_url}/chat/routes")
                response.raise_for_status()
                return response.json().get("data", {"routes": []})
            except Exception as e:
                logger.error(f"Failed to fetch routes from API: {e}")
                # Return empty list so the fallback keyboard kicks in
                return {"routes": []}

    async def get_workers_status(self) -> dict:
        """Fetches the health status of configured workers."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(f"{self.base_url}/chat/workers/status")
                response.raise_for_status()
                return response.json().get("data", {}).get("workers", {})
            except Exception as e:
                logger.error(f"Failed to fetch workers status: {e}")
                return {}

    async def get_session_info(self, telegram_id: int) -> dict:
        """Fetches the active session info (current route, image status)."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self.base_url}/chat/session", params={"telegram_id": telegram_id})
                response.raise_for_status()
                return response.json().get("data", {"active_session": False})
            except Exception as e:
                logger.error(f"Failed to fetch session info: {e}")
                return {"active_session": False}

    async def set_session_route(self, telegram_id: int, route: str) -> bool:
        """Explicitly sets the active worker route for the current session."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.post(f"{self.base_url}/chat/session/route", json={"telegram_id": telegram_id, "route": route})
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Failed to set session route: {e}")
                return False

    async def send_message(self, telegram_id: int, text: str | None = None, images_bytes: list[tuple[str, bytes]] | None = None, route: str | None = None) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            data = {
                "telegram_id": telegram_id
            }
            if route:
                data["route"] = route
            if text:
                data["text"] = text
            
            files = []
            if images_bytes:
                for file_name, img_bytes in images_bytes:
                    files.append(("images", (file_name, img_bytes, "image/jpeg")))

            try:
                response = await client.post(f"{self.base_url}/chat/message", data=data, files=files)
                response.raise_for_status()
                result = response.json()
                # Use the new nested format from Phase 1, fallback to old if not found
                data_dict = result.get("data", {})
                return data_dict.get("response", result.get("response", "No response from AI."))
            except httpx.TimeoutException:
                logger.error("Timeout connecting to local API")
                return "The local MedGemma server is taking too long to respond. Please try again later."
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    return "You are not authorized to use this bot."
                logger.error(f"HTTP error from local API {e.response.status_code}: {e.response.text}")
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

    async def send_batch(self, telegram_id: int, images_bytes: list[bytes], route: str, text: str | None = None) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            data = {
                "telegram_id": telegram_id,
                "route": route
            }
            if text:
                data["text"] = text
            
            files = [
                ("images", (f"image_{i}.jpg", img_bytes, "image/jpeg"))
                for i, img_bytes in enumerate(images_bytes)
            ]

            try:
                response = await client.post(f"{self.base_url}/chat/batch", data=data, files=files)
                response.raise_for_status()
                result = response.json()
                data_dict = result.get("data", {})
                return data_dict.get("message", "Batch submitted successfully.")
            except httpx.TimeoutException:
                logger.error("Timeout connecting to local API during batch upload")
                return "Upload timed out. Please try again."
            except Exception as e:
                logger.error(f"Error submitting batch: {e}")
                return "Failed to submit batch for processing."

    async def cancel_batch(self, telegram_id: int) -> bool:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.request(
                    "DELETE", 
                    f"{self.base_url}/chat/batch", 
                    json={"telegram_id": telegram_id}
                )
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Error canceling batch: {e}")
                return False

api_client = APIClient()
