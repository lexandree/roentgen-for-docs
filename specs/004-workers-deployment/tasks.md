# Tasks: Workers and Deployment

- [x] T001 [P] Standardize payload in `src/api/routes/chat.py` (ensure it consistently sends multimodal OpenAI format).
- [x] T002 [P] Refine `src/api/worker.py` to correctly unpack and process multimodal messages and return telemetry.
- [x] T003 [P] Implement `src/workers/cloud_adapter.py` for Google Drive polling and inference.
- [x] T004 [P] Create `src/api/Dockerfile` (Dispatcher API).
- [x] T005 [P] Create `src/bot/Dockerfile` (Telegram Bot).
- [x] T006 [P] Create root `docker-compose.yml` for orchestration.
- [x] T007 [P] Create `.dockerignore` for both services.
- [x] T008 [P] Update `README.md` with Docker and worker instructions.
- [x] T009 [P] Implement telemetry collection (latency, tokens) in `MedGemmaModel`.
- [x] T010 [P] Implement parameterized session timeout (default configurable in `.env`).
- [x] T011 [P] Add `/end` command to bot to manually terminate conversation sessions.
