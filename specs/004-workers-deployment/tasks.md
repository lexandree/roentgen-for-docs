# Tasks: Workers and Deployment

- [ ] T001 [P] Standardize payload in `src/api/routes/chat.py` (ensure it consistently sends multimodal OpenAI format).
- [ ] T002 [P] Refine `src/api/worker.py` to correctly unpack and process multimodal messages.
- [ ] T003 [P] Implement `src/workers/cloud_adapter.py` for Google Drive polling and inference.
- [ ] T004 [P] Create `src/api/Dockerfile` (Dispatcher API).
- [ ] T005 [P] Create `src/bot/Dockerfile` (Telegram Bot).
- [ ] T006 [P] Create root `docker-compose.yml` for orchestration.
- [ ] T007 [P] Create `.dockerignore` for both services to exclude unnecessary files.
- [ ] T008 [P] Update `README.md` with Docker instructions.
