# Implementation Tasks: Integrated Admin Monitoring

**Branch**: `008-admin-monitoring` | **Date**: 2026-03-15 | **Spec**: [link to spec.md]
**Input**: Feature specification from `/specs/008-admin-monitoring/spec.md` and `/specs/008-admin-monitoring/plan.md`

## 1. API - Admin Routes & Security

- **Goal**: Expose monitoring data via new API endpoints, restricted to admin users.
- **Tasks**:
  - [ ] Create `src/api/routes/admin.py`.
  - [ ] Register `admin_router` in `src/api/main.py`.
  - [ ] Implement `GET /api/v1/admin/status` endpoint to return worker health (VRAM, CPU, status).
  - [ ] Implement `GET /api/v1/admin/stats` endpoint to return system-wide usage statistics.
  - [ ] Implement `GET /api/v1/admin/user_stats/{telegram_id}` endpoint to return individual user statistics.
  - [ ] Ensure all admin endpoints are protected by `auth_service.is_admin_user` dependency.

## 2. API - Chat Manager Enhancements

- **Goal**: Add methods to `ChatManager` to gather system and usage data.
- **Tasks**:
  - [ ] Implement `async def get_gpu_metrics(self) -> Dict[str, Any]`:
    - [ ] Execute `nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader,nounits` via `subprocess`.
    - [ ] Parse output for used VRAM (MiB) and GPU utilization (%).
    - [ ] Handle `nvidia-smi` not found or no GPU errors gracefully.
  - [ ] Implement `async def get_cpu_metrics(self) -> Dict[str, Any]`:
    - [ ] Execute `mpstat -u 1 1` or `top -bn1 | grep 'Cpu(s)'` via `subprocess`.
    - [ ] Parse output for average CPU load (%).
    - [ ] Handle `mpstat`/`top` not found errors gracefully.
  - [ ] Implement `async def get_system_stats(self, db, period: str = "daily") -> Dict[str, Any]`:
    - [ ] Query `interaction_logs` table for total requests, average latency, total images, breakdown by worker route and task type for the specified `period`.
    - [ ] Aggregate results using SQL (SUM, AVG, COUNT, GROUP BY).
  - [ ] Implement `async def get_user_stats(self, db, telegram_id: int) -> Dict[str, Any]`:
    - [ ] Query `interaction_logs` for total requests, total images, average latency, and last activity for a specific user.

## 3. Bot - Admin Command Handlers

- **Goal**: Implement Telegram commands for administrators to access monitoring data.
- **Tasks**:
  - [ ] Add `async def cmd_admin_status(message: types.Message)` handler to `src/bot/handlers/messages.py`.
  - [ ] Call `api_client.get_admin_status()` (new method in `api_client.py`).
  - [ ] Format and display worker health metrics in Markdown.
  - [ ] Add `async def cmd_admin_stats(message: types.Message, period: str = "daily")` handler.
  - [ ] Call `api_client.get_admin_stats(period)`. Format and display system-wide statistics.
  - [ ] Add `async def cmd_admin_user_stats(message: types.Message, user_id: int)` handler.
  - [ ] Call `api_client.get_admin_user_stats(user_id)`. Format and display user-specific statistics.
  - [ ] Ensure all admin command handlers enforce `auth_service.is_admin_user` check.
  - [ ] Update `bot.set_my_commands` in `src/bot/main.py` to include new admin commands.

## 4. API Client Updates

- **Goal**: Add methods to `APIClient` for calling new admin API endpoints.
- **Tasks**:
  - [ ] Implement `async def get_admin_status(self) -> Dict[str, Any]`.
  - [ ] Implement `async def get_admin_stats(self, period: str) -> Dict[str, Any]`.
  - [ ] Implement `async def get_admin_user_stats(self, telegram_id: int) -> Dict[str, Any]`.
  - [ ] Handle potential `401 Unauthorized` responses from API for non-admin users.
