import pytest
import httpx
from src.bot.services.api_client import APIClient
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_api_client_timeout():
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Timeout")):
        client = APIClient()
        response = await client.send_message(12345, text="Hello")
        assert "taking too long" in response
