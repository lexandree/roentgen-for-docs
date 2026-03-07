import pytest
import asyncio
from src.api.workers.session_cleaner import SessionCleaner
from src.api.db.database import get_db

@pytest.mark.asyncio
async def test_session_cleanup():
    # This is a unit test for the cleaner logic
    # In a real test, we would insert an old session and verify it gets deleted
    pass
