# Tasks: Convert whitelist to JSON user configs

- [x] T001 [P] Expand `User` model in `src/api/db/models.py` with `system_prompt_type`, `role`, `allowed_workers`, `daily_limit`, `specialty`. Add `SystemPrompt` model.
- [x] T002 [P] Modify `init_db` in `src/api/db/database.py` to safely add new columns to the `users` table and create `system_prompts` table.
- [x] T003 [P] Update `src/shared/services/gdrive_whitelist.py` to parse JSON and return a dictionary containing both `users` and `prompts`.
- [x] T004 [P] Update `src/api/services/auth.py` to correctly store JSON configs into the SQLite database, syncing both users and system prompts. Add `get_system_prompt` method.
- [x] T005 [P] Update `src/bot/services/auth.py` to cache the dict configs and update `is_user_whitelisted`. Add `get_user` method.
- [x] T006 [P] Secure `/refresh_whitelist` in `src/bot/handlers/messages.py` to only allow users with `role == 'admin'`.
- [x] T007 [P] Update API `chat.py` to check `allowed_workers` in `User` before dispatching to workers, and fetch the correct dynamic system prompt text based on user settings.
- [x] T008 [P] Update `src/api/scripts/init_db.py` to populate new fields if adding a user via CLI.
- [x] T009 [P] Update `chat_manager.py`'s `dispatch_inference_to_worker` to accept a dynamic system prompt text parameter.
- [x] T010 [P] Update tests to reflect new dictionary whitelist format.