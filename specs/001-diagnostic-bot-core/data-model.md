# Data Model: Diagnostic Bot Core

## Entities

### User (Whitelist)
Represents a doctor who is authorized to use the system. Managed locally.
- `telegram_id` (Integer, Primary Key)
- `name` (String)
- `is_active` (Boolean) - Default True
- `created_at` (DateTime)

### Session Context
Represents the current active session for a specific user. Managed locally.
- `session_id` (String/UUID, Primary Key)
- `telegram_id` (Integer, Foreign Key)
- `last_activity` (DateTime) - Used to enforce the 24-hour expiry rule (FR-008).
- `has_active_image` (Boolean) - Indicates if an image has been vectorized and is currently loaded in the model's KV-cache. Physical images are deleted immediately after vectorization.

### Message History
Represents the chronological discussion between the doctor and the AI within a session. Managed locally.
- `message_id` (Integer, Primary Key)
- `session_id` (String/UUID, Foreign Key)
- `role` (String) - 'user' or 'assistant'
- `content` (String) - The text of the message or the AI's response.
- `timestamp` (DateTime)

## Validation Rules
- All incoming requests to the local API MUST include a valid `telegram_id` that exists in the User whitelist.
- If `last_activity` is older than 24 hours, the session (including database history and in-memory KV-cache) MUST be cleared.

## State Transitions
- **Session Creation**: When a user sends a message and no active session exists (or the previous one expired), a new session is created.
- **Image Vectorization**: When an image is uploaded, it is processed into visual embeddings by MedGemma, stored in the model's KV-cache, and the physical file is immediately deleted from the disk. `has_active_image` is set to True.
- **Session Expiry**: When 24 hours pass without activity, an active cleanup worker transitions the session to an expired state, wipes its text data from the DB, and clears its KV-cache from the model.
- **Manual Clear**: The user can trigger an immediate wipe via the `/clear` command.