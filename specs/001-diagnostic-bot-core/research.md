# Phase 0: Outline & Research

## Research Areas & Decisions

### 1. Bot Frontend State Management
- **Decision**: The Telegram bot (Oracle Cloud) will be entirely stateless. It will hold NO session data, NO history, and NO images persistently.
- **Rationale**: Strict adherence to Constitution Principle I (Security First) and Principle VI (Stateless Design). Any session state, conversation history, or authorization checks will be performed on the local server. The bot will simply forward the `telegram_id` and payload.
- **Alternatives considered**: Keeping a temporary Redis cache on Oracle Cloud for rate limiting or session tracking was rejected due to privacy concerns.

### 2. Local Server API Framework
- **Decision**: `FastAPI`
- **Rationale**: FastAPI is asynchronous, modern, and provides automatic OpenAPI documentation which is excellent for defining the contract between the bot and the local server. It integrates perfectly with Pydantic for validation.
- **Alternatives considered**: Flask (synchronous, slower), Django (too heavy for a simple inference API).

### 3. Session and History Storage
- **Decision**: `SQLite` with asynchronous drivers (`aiosqlite`).
- **Rationale**: The scale is small (a few doctors). SQLite is a zero-configuration, serverless database that lives securely on the local machine. It perfectly handles the requirement for storing conversation history and the user whitelist without needing a separate database service.
- **Alternatives considered**: PostgreSQL (overkill for this MVP), Redis (good for expiry, but SQLite is simpler to deploy as a single file).

### 4. Handling File Transfers (Images)
- **Decision**: The bot will download the image from Telegram into memory (`BytesIO`), encode it as Base64 (or send as multipart/form-data), forward it to the local FastAPI server via HTTP POST, and then immediately discard the memory buffer.
- **Rationale**: Prevents any files from touching the disk on the Oracle Cloud server.
- **Alternatives considered**: Saving the file to `/tmp` and deleting it after. Rejected because writing to disk is riskier than keeping it in memory.
