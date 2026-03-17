# Tasks: Multi Model Dispatcher

**Input**: Design documents from `/specs/002-multi-model-dispatcher/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency verification.

- [x] T001 Verify and update `requirements.txt` for `aiogram` FSM and `google-api-python-client` in `src/api/requirements.txt` and `src/bot/requirements.txt`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

- [x] T002 Create `InteractionLog` model definition in `src/api/db/models.py`.
- [x] T003 Update `src/api/scripts/init_db.py` to create the `interaction_logs` table without dropping existing data.
- [x] T004 [P] Define `AnalysisSession` FSM states (`waiting_for_route`, `waiting_for_batch_images`) in `src/bot/states.py` (create file).
- [x] T005 [P] Configure `MemoryStorage` for aiogram FSM dispatcher in `src/bot/main.py`.

**Checkpoint**: Foundation ready - database and FSM storage are configured.

---

## Phase 3: User Story 1 - Quick Analysis (Single Image) (Priority: P1) 🎯 MVP

**Goal**: Quickly analyze a single medical image using local server with immediate routing options.

**Independent Test**: Send a single photo. The bot should immediately offer routing options including the fast local server. Selecting it should process the image and return the result.

### Implementation for User Story 1

- [x] T006 [P] [US1] Update `POST /api/v1/chat/message` to accept an optional `route` parameter in `src/api/routes/chat.py`.
- [x] T007 [P] [US1] Update `src/bot/services/api_client.py` to pass the `route` parameter in `send_message`.
- [x] T008 [US1] Modify photo handler in `src/bot/handlers/images.py` to intercept single images (reject documents), save photo and caption to FSM state (clearing any previous active single-image request), and present inline routing keyboard.
- [x] T009 [US1] Implement callback query handler in `src/bot/handlers/messages.py` (or a new callbacks handler) to process route selection, retrieve image from FSM, and send to backend.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Batch/Series Analysis (Multiple Images) (Priority: P2)

**Goal**: Upload a series of images (e.g., MRI slices) or an album and process them together using a powerful remote server (Colab or RunPod).

**Independent Test**: Use the `/analyze` command or send an album directly to receive a batch routing menu and queue the batch for processing.

### Implementation for User Story 2

- [x] T010 [P] [US2] Create `src/shared/services/gdrive_storage.py` to manage isolated user subfolders and file uploads/deletions on Google Drive.
- [x] T011 [P] [US2] Implement new `POST /api/v1/chat/batch` endpoint in `src/api/routes/chat.py` that delegates to `gdrive_storage.py`.
- [x] T012 [P] [US2] Implement new `DELETE /api/v1/chat/batch` endpoint in `src/api/routes/chat.py` to cancel and clean up Google Drive folders.
- [x] T013 [P] [US2] Add `send_batch` and `cancel_batch` methods to `src/bot/services/api_client.py`.
- [x] T014 [US2] Implement 5-second debounce logic for `media_group_id` in `src/bot/handlers/images.py` using `asyncio.sleep` or FSM data, storing captions, and presenting a batch routing menu (explicitly hiding the "Local" route) after timeout.
- [x] T015 [US2] Implement `/analyze` command handler in `src/bot/handlers/messages.py` to manually enter batch FSM state.
- [x] T016 [US2] Update `/clear` command in `src/bot/handlers/messages.py` to cancel active batch FSM state and call `api_client.cancel_batch`.
- [x] T017 [US2] Implement logic to reject uploads exceeding the 20-image limit in `src/bot/handlers/images.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Usage Analytics and Monitoring (Priority: P3)

**Goal**: Log every interaction (user, chosen route, number of images, duration) to monitor system load and track usage.

**Independent Test**: Complete any analysis task and verify a new record is created in the database containing the correct metadata.

### Implementation for User Story 3

- [x] T018 [P] [US3] Add DB logging to `POST /api/v1/chat/message` (status `queued` -> `processing` -> `completed`/`failed`) in `src/api/routes/chat.py`.
- [x] T019 [P] [US3] Add DB logging to `POST /api/v1/chat/batch` in `src/api/routes/chat.py`.
- [x] T020 [US3] Update `src/api/services/inference.py` to ensure it returns appropriate success/failure states so routes can log terminal statuses accurately with `completed_at` timestamps.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [x] T021 Verify no sensitive medical data is logged in `interaction_logs`.
- [x] T022 Test network timeout scenarios and graceful degradation when communicating with external routes.
- [x] T023 Verify user context isolation is robust (FSM states do not leak between users).
- [x] T024 Add validation in `src/bot/handlers/images.py` and `messages.py` to explicitly reject document attachments that are not valid images.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion. BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion. User Story 1 must be completed first as MVP, then User Story 2, then User Story 3 adds tracking to both.
- **Polish (Final Phase)**: Depends on all user stories being complete.

### Parallel Opportunities

- Foundational tasks T004 and T005 can be done in parallel with DB tasks T002 and T003.
- US1 FastAPI changes (T006, T007) can be done in parallel with bot handler changes.
- US2 Drive storage (T010) and endpoints (T011, T012) can be built independently of bot debounce logic (T014).
- US3 DB logging tasks can be added to endpoints simultaneously.