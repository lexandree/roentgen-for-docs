# Implementation Tasks: Integrated Admin Monitoring

**Branch**: `006-admin-monitoring` | **Date**: 2026-03-16 | **Spec**: [link to spec.md]
**Input**: Feature specification from `/specs/006-admin-monitoring/spec.md` and `/specs/006-admin-monitoring/plan.md`

## 1. API - Admin Routes & Security

- **Goal**: Expose monitoring data via new API endpoints, restricted to admin users.
- **Tasks**:
  - [x] Create `src/api/routes/admin.py`.
  - [x] Register `admin_router` in `src/api/main.py`.
  - [x] Implement `GET /api/v1/admin/status` endpoint to return worker application health (HTTP ping latency).
  - [x] Implement `GET /api/v1/admin/stats` endpoint to return system-wide usage statistics.
  - [x] Implement `GET /api/v1/admin/user_stats/{telegram_id}` endpoint to return individual user statistics (including session duration).
  - [x] Ensure all admin endpoints are protected by `auth_service.is_admin_user` dependency.

## 2. API - Chat Manager Enhancements

- **Goal**: Add methods to `ChatManager` to gather application health and business data.
- **Tasks**:
  - [x] Implement `async def ping_workers(self) -> Dict[str, Any]`:
    - [x] Iterate through configured workers and issue an HTTP GET to their `/health` or base URL.
    - [x] Record the response time (latency) or "Timeout/Offline" status.
  - [x] Implement `async def get_system_stats(self, db, period: str = "daily") -> Dict[str, Any]`:
    - [x] Query `interaction_logs` table for total requests, average latency, total images, breakdown by worker route for the specified `period`.
  - [x] Implement `async def get_user_stats(self, db, telegram_id: int) -> Dict[str, Any]`:
    - [x] Query `interaction_logs` for total requests, total images, and average latency.
    - [x] **Calculate Session Duration**: Implement logic (SQL or Python) to group user interactions into "sessions" (e.g., gaps > 30 mins split sessions) and sum the total active time for the user.

## 3. Bot - Admin Command Handlers

- **Goal**: Implement Telegram commands for administrators to access monitoring data.
- **Tasks**:
  - [x] Add `async def cmd_admin_status(message: types.Message)` handler to `src/bot/handlers/messages.py`.
  - [x] Call `api_client.get_admin_status()` and display worker ping/health metrics in Markdown.
  - [x] Add `async def cmd_admin_stats(message: types.Message, period: str = "daily")` handler.
  - [x] Call `api_client.get_admin_stats(period)` and display system-wide statistics.
  - [x] Add `async def cmd_admin_user_stats(message: types.Message, user_id: int)` handler.
  - [x] Call `api_client.get_admin_user_stats(user_id)` and display user-specific statistics, highlighting the **total session duration**.
  - [x] Ensure all admin command handlers enforce `auth_service.is_admin_user` check.
  - [x] Update `bot.set_my_commands` in `src/bot/main.py` to include new admin commands.

## 4. API Client Updates

- **Goal**: Add methods to `APIClient` for calling new admin API endpoints.
- **Tasks**:
  - [x] Implement `async def get_admin_status(self) -> Dict[str, Any]`.
  - [x] Implement `async def get_admin_stats(self, period: str) -> Dict[str, Any]`.
  - [x] Implement `async def get_admin_user_stats(self, telegram_id: int) -> Dict[str, Any]`.
  - [x] Handle potential `401 Unauthorized` responses from API for non-admin users.

## 5. Worker Statistics Extension

- **Goal**: Provide admin commands for worker usage tracking.
- **Tasks**:
  - [ ] `chat_manager.py`: Add `get_worker_stats(db, period)` to aggregate tokens and requests by `route`.
  - [ ] `admin.py`: Add `GET /api/v1/admin/worker_stats` endpoint.
  - [ ] `api_client.py`: Add `get_admin_worker_stats(period)`.
  - [ ] `messages.py`: Add `cmd_admin_worker_stats` handler for `/admin_worker_stats` command.
  - [ ] `main.py`: Add `/admin_worker_stats` to command list.
