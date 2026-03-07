# roentgen_for_docs Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-07

## Active Technologies
- Python 3.12+ (managed via Conda) + `aiogram` (bot framework), `FastAPI` (local inference API), `httpx` (async HTTP client for bot), `pydantic` (data validation), `google-api-python-client` (for Google Drive whitelist fetch) (001-diagnostic-bot-core)
- SQLite (for managing user sessions, context history, and caching the whitelist on the local server), Google Drive (source of truth for whitelist) (001-diagnostic-bot-core)

- Python 3.12+ (managed via Conda) + `aiogram` (bot framework), `FastAPI` (local inference API), `httpx` (async HTTP client for bot), `pydantic` (data validation) (001-diagnostic-bot-core)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12+ (managed via Conda): Follow standard conventions

## Recent Changes
- 001-diagnostic-bot-core: Added Python 3.12+ (managed via Conda) + `aiogram` (bot framework), `FastAPI` (local inference API), `httpx` (async HTTP client for bot), `pydantic` (data validation), `google-api-python-client` (for Google Drive whitelist fetch)

- 001-diagnostic-bot-core: Added Python 3.12+ (managed via Conda) + `aiogram` (bot framework), `FastAPI` (local inference API), `httpx` (async HTTP client for bot), `pydantic` (data validation)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
