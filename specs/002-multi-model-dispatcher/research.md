# Research: Multi Model Dispatcher

**Feature Branch**: `002-multi-model-dispatcher`  
**Date**: 2026-03-08

## Topic: aiogram 3.x Media Group Handling & FSM (5-second window)
- **Decision**: Use a combination of `aiogram`'s `FSMContext` (with an `AnalysisSession` state group) and an `asyncio.sleep` task or `Cache` to debounce media group items, accumulating them until 5 seconds have passed without new items. 
- **Rationale**: Telegram sends albums as individual messages sharing the same `media_group_id`. To process them as a batch and show only one menu, we must "wait" for the burst to finish. Using an asyncio task that is refreshed/cancelled on each new item in the group is a standard, non-blocking pattern in `aiogram` 3.
- **Alternatives considered**: Middlewares (too complex for a simple state machine), database tracking (too slow, excessive writes for a 5-second window).

## Topic: Database Structure for interaction_logs (SQLite + aiosqlite)
- **Decision**: Create an `interaction_logs` table via `init_db.py` (using raw SQL execution with `aiosqlite` as currently implemented) holding fields like `telegram_id`, `route`, `task_type`, `images_count`, `status`, `created_at`, `completed_at`.
- **Rationale**: Fits perfectly with the existing lightweight `sqlite+aiosqlite` setup. No heavy ORM required since the schema is simple and performance needs are low (single-user bot currently, minimal concurrent DB writes).
- **Alternatives considered**: SQLAlchemy/Tortoise ORM (overkill for the current scope).

## Topic: Google Drive Isolated Folders
- **Decision**: Use `google-api-python-client` with the existing Service Account credentials. Create a subfolder under a root 'MedGemma Batches' folder named with the `telegram_id`. Store batch images there. On batch cancellation, query for this specific folder ID and issue a `files().delete()` call.
- **Rationale**: Direct integration with the API allows clean separation of context (Principle IV). Deleting the folder atomically guarantees no residual medical data is left behind.
- **Alternatives considered**: Storing all images in a flat structure with prefixes (harder to delete atomically, messy).