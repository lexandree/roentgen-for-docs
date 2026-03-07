---
description: "Task list template for feature implementation"
---

# Tasks: Diagnostic Bot Core

**Input**: Design documents from `/specs/001-diagnostic-bot-core/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included as requested implicitly by the test criteria in spec and plan.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Frontend/Bot**: `src/bot/` (Oracle Cloud)
- **Backend/API**: `src/api/` (Local Server)
- **Tests**: `tests/bot/` and `tests/api/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure for `src/bot/`, `src/api/`, `tests/bot/`, and `tests/api/`
- [x] T002 [P] Initialize Python dependencies in `src/bot/requirements.txt`
- [x] T003 [P] Initialize Python dependencies in `src/api/requirements.txt`
- [x] T004 [P] Setup configuration loading in `src/bot/config.py` and `src/api/config.py` (including Google Drive API credentials via secure environment variables)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Setup SQLite database connection and schema models in `src/api/db/database.py` and `src/api/db/models.py` (User, Session Context, Message History)
- [x] T006 [P] Implement Google Drive whitelist fetching service in `src/shared/services/gdrive_whitelist.py` (shared logic for both bot and API)
- [x] T007 [P] Implement whitelist verification and sync logic in `src/api/services/auth.py` (backend verification)
- [x] T008 [P] Implement bot-side whitelist caching and verification in `src/bot/services/auth.py` (frontend rejection)
- [x] T009 Initialize FastAPI app in `src/api/main.py` (including startup whitelist sync)
- [x] T010 Initialize aiogram bot application in `src/bot/main.py` (including startup whitelist sync)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Text-Based Medical Query (Priority: P1) 🎯 MVP

**Goal**: As a doctor, I want to send a text query to the Telegram bot to get general medical AI assistance or discuss a case without necessarily uploading an image first.

**Independent Test**: Can be tested by starting a new session and sending a purely text-based medical question. The bot must respond coherently using the MedGemma model.

### Tests for User Story 1

- [x] T011 [P] [US1] Write contract test for text POST to `/chat/message` in `tests/api/test_chat_endpoint.py`
- [x] T012 [P] [US1] Write integration test for bot text message handling in `tests/bot/test_message_handler.py`

### Implementation for User Story 1

- [x] T013 [P] [US1] Implement MedGemma inference service mock/wrapper for text in `src/api/services/inference.py`
- [x] T014 [US1] Implement chat session and history management in `src/api/services/chat_manager.py` (depends on T005)
- [x] T015 [US1] Implement `POST /chat/message` endpoint for text in `src/api/routes/chat.py`
- [x] T016 [P] [US1] Implement local API HTTP client for sending text in `src/bot/services/api_client.py`
- [x] T017 [US1] Implement Telegram text message handler in `src/bot/handlers/messages.py`

**Checkpoint**: At this point, User Story 1 should be fully functional. Doctors can send text messages and get AI responses.

---

## Phase 4: User Story 2 - Image-Based Diagnostic Analysis (Priority: P1)

**Goal**: As a doctor, I want to upload an X-ray or MRI image to the Telegram bot at any point in the conversation, so that MedGemma can analyze it and establish visual context for further discussion.

**Independent Test**: Can be tested by uploading an image (either as the first message or mid-conversation). The bot must acknowledge the image, process it, and return a diagnostic report.

### Tests for User Story 2

- [x] T018 [P] [US2] Write contract test for image multipart POST to `/chat/message` in `tests/api/test_chat_endpoint.py`
- [x] T019 [P] [US2] Write test for bot image downloading and forwarding in `tests/bot/test_image_handler.py`

### Implementation for User Story 2

- [x] T020 [P] [US2] Update MedGemma inference service to process image files in `src/api/services/inference.py`
- [x] T021 [US2] Implement temporary file saving for uploaded images in `src/api/services/chat_manager.py`
- [x] T022 [US2] Update `POST /chat/message` endpoint to handle multipart/form-data images in `src/api/routes/chat.py`
- [x] T023 [P] [US2] Update local API HTTP client to stream image buffers in `src/bot/services/api_client.py`
- [x] T024 [US2] Implement Telegram photo handler to download into memory and forward in `src/bot/handlers/images.py`
- [x] T025 [US2] Add message deflection for unsupported formats (e.g. documents) in `src/bot/handlers/messages.py`

**Checkpoint**: User Stories 1 AND 2 should both work independently. Text and Image processing is functional.

---

## Phase 5: User Story 3 - Handling Connectivity & Privacy (Priority: P2)

**Goal**: As a doctor, I want my sessions to be completely isolated from others, and I want clear error messages if the local MedGemma server is slow or unreachable, so I can trust the system's reliability and security.

**Independent Test**: Test isolation by having two users send queries simultaneously. Test connectivity by severing the Oracle-to-Local tunnel during an active discussion.

### Tests for User Story 3

- [x] T026 [P] [US3] Write integration test for session timeouts and context isolation in `tests/api/test_isolation.py`
- [x] T027 [P] [US3] Write test for handling 30s timeouts in `tests/bot/test_api_client.py`

### Implementation for User Story 3

- [x] T028 [US3] Implement active 24-hour inactivity session cleanup worker (e.g., using APScheduler or FastAPI background tasks) in `src/api/workers/session_cleaner.py`
- [x] T029 [US3] Implement `POST /chat/clear` endpoint in `src/api/routes/chat.py`
- [x] T030 [P] [US3] Implement `/clear` command handler in `src/bot/handlers/commands.py`
- [x] T031 [P] [US3] Implement `/refresh_whitelist` command handler in `src/bot/handlers/commands.py` to re-fetch from Google Drive
- [x] T032 [US3] Add strict 30s timeout and exception catching (e.g. `httpx.TimeoutException`) to `src/bot/services/api_client.py`
- [x] T033 [US3] Implement graceful error replies for users on network failure in all bot handlers

**Checkpoint**: The bot securely isolates context, enforces 24h timeouts, and handles tunnel disconnections gracefully.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T034 [P] Verify no images are persistently logged or stored on the Oracle Cloud server (Constitution check)
- [x] T035 Ensure local physical images are deleted immediately after vectorization into KV-cache in `src/api/services/inference.py`
- [x] T036 Implement `src/api/scripts/init_db.py` to easily add whitelisted Telegram IDs
- [x] T037 Validate `/clear` and 24h session active cleanup worker properly removes session data (text history and KV-cache references) from memory and DB

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 can theoretically proceed in parallel once Phase 2 is done.
  - US3 depends heavily on US1/US2 implementations to enforce limits.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### Parallel Opportunities

- Setup requirements creation (T002, T003) can be done in parallel.
- Contract tests for both Bot and API can be drafted simultaneously.
- Bot API Client (`src/bot/services/api_client.py`) and Local API routes (`src/api/routes/chat.py`) can be developed concurrently based on the agreed-upon contract `local-inference-api.md`.

---

## Implementation Strategy

### MVP First (User Story 1 & 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Text queries)
4. Complete Phase 4: User Story 2 (Image uploads)
5. **STOP and VALIDATE**: Verify that the core bridge logic correctly routes both modalities to the local GPU server.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy text-only MVP
3. Add User Story 2 → Test independently → Image support enabled
4. Add User Story 3 → Test independently → Hardened edge-cases & privacy constraints
5. Each story adds value without breaking previous stories
