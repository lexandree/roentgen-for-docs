# Implementation Plan: Convert whitelist to JSON user configs

## Approach
1. **Model Definition**: Expand the `User` model in `src/api/db/models.py` to include `system_prompt_type` (int), `role` (str), `allowed_workers` (list/JSON), `daily_limit` (int), `specialty` (str). Add a `SystemPrompt` model.
2. **Database Migration**: Update `init_db` in `src/api/db/database.py` to add new fields to the `users` table and create a new `system_prompts` table.
3. **Whitelist Fetch Service**: Refactor `src/shared/services/gdrive_whitelist.py` to parse JSON and return both a `users` dict and a `prompts` dict. Support legacy flat JSON for backwards compatibility.
4. **Auth Sync**: Update `src/api/services/auth.py` to sync both user configs and system prompts into the SQLite database. Add a method to fetch system prompts by ID.
5. **Bot Auth Cache**: Update `src/bot/services/auth.py` to cache the dict configs and provide a `get_user` method.
6. **Enforcement (Bot)**: Update `src/bot/handlers/messages.py`, `src/bot/handlers/images.py` to check `is_active` and `admin` roles where appropriate. Update `/refresh_whitelist` command to restrict to `admin` role.
7. **Enforcement & Prompts (API)**: Ensure API `chat.py` endpoint respects `allowed_workers` configuration when routing requests to workers. Fetch the dynamic system prompt based on user's `system_prompt_type` and pass it to `chat_manager`.
8. **Chat Manager**: Update `src/api/services/chat_manager.py` to accept the dynamic system prompt string instead of using a hardcoded one.

## Scope & Constraints
- Retain existing `whitelist_file_id` config mechanism. The only change is the contents and parsing method of the file itself.
- SQLite does not have a native array type; `allowed_workers` should be stored as a comma-separated string or a JSON text field.

## Dependencies
- `google-api-python-client` and `aiosqlite` (already in use).
- Changes affect bot and API processes; restarting both may be required during dev.