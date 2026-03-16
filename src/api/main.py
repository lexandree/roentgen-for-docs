from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from src.api.db.database import init_db, get_db
from src.api.services.auth import auth_service
from src.api.routes.chat import router as chat_router
from src.api.routes.admin import router as admin_router
from src.api.workers.session_cleaner import session_cleaner

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # We need a db connection to sync whitelist
    async for db in get_db():
        await auth_service.sync_whitelist(db)
        break # just run once on startup
    
    # Start background cleaner
    session_cleaner.start()
    
    yield

app = FastAPI(title="MedGemma Local API", lifespan=lifespan)
app.include_router(chat_router)
app.include_router(admin_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}