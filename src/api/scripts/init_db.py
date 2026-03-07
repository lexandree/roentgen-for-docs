import asyncio
import argparse
import aiosqlite
import sys
import os

# Add parent directory to sys.path to allow importing from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.api.db.database import init_db, settings

async def add_user(telegram_id: int, name: str | None = None):
    db_path = settings.db_path.replace("sqlite+aiosqlite:///", "")
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO users (telegram_id, name, is_active) VALUES (?, ?, 1) ON CONFLICT(telegram_id) DO UPDATE SET is_active=1",
            (telegram_id, name)
        )
        await db.commit()
    print(f"User {telegram_id} ({name or 'N/A'}) added to whitelist.")

async def main():
    parser = argparse.ArgumentParser(description="Initialize MedGemma local DB.")
    parser.add_argument("--init", action="store_true", help="Initialize tables")
    parser.add_argument("--add-user", type=int, help="Telegram ID to whitelist")
    parser.add_argument("--name", type=str, help="Name for the user")
    
    args = parser.parse_args()
    
    if args.init:
        await init_db()
        print("Database tables initialized.")
        
    if args.add_user:
        await add_user(args.add_user, args.name)

if __name__ == "__main__":
    asyncio.run(main())
