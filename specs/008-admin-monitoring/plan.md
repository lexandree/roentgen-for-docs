# Implementation Plan: Integrated Admin Monitoring

**Branch**: `008-admin-monitoring` | **Date**: 2026-03-15 | **Spec**: [link to spec.md]
**Input**: Feature specification from `/specs/008-admin-monitoring/spec.md`

## Summary

Implement a suite of administrative commands within the existing Telegram bot to provide real-time worker health status and usage statistics. This involves adding new API endpoints for data exposure and new bot handlers for command parsing, with strict role-based access control.

## Technical Context

**Language/Version**: Python 3.12+ (FastAPI dispatcher, Aiogram bot)
**Primary Dependencies**: `httpx`, `aiosqlite`, `subprocess` (for system commands)
**Target Platform**: Linux servers (Cloud for bot/dispatcher, Local for GPU worker).
**Project Type**: Web-service (Dispatcher API & Telegram Bot)
**Constraints**: 
- Securely parse `nvidia-smi` and `top`/`mpstat` output without breaking the application.
- Ensure database queries are efficient for real-time and aggregated statistics.
- Maintain low latency for admin commands.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Does it ensure patient data confidentiality? (Principle I: Security First) - *Only aggregated/admin-level data, no raw patient info.*
- [x] Are Telegram handlers, API logic, and inference separated? (Principle II: Modularity) - *New admin API routes, new bot handlers.*
- [x] Is graceful error handling implemented for network timeouts? (Principle III: Robustness) - *System command parsing errors must be handled.*
- [x] Is user context isolated? (Principle IV: Privacy) - *Admin access strictly enforced.*
- [x] Is the Telegram bot acting as a lightweight relay? (Principle VI: Stateless/Stateful Design) - *Bot remains a relay; heavy logic is in API.*

## Project Structure

### Documentation (this feature)

```text
specs/008-admin-monitoring/
├── plan.md              
├── spec.md        
└── tasks.md             
```

### Source Code

```text
src/
├── api/
│   ├── routes/
│   │   └── admin.py      # NEW: Endpoints for admin queries (stats, worker health)
│   └── services/
│       └── chat_manager.py # NEW methods for aggregated stats and system health checks
└── bot/
    └── handlers/
        └── messages.py   # NEW: Handlers for /admin_status, /admin_stats, /admin_user_stats
```

**Structure Decisions**:
1.  **New `admin.py` route file:** Isolates admin-specific API endpoints from general chat routing.
2.  **`ChatManager` for system health**: Centralizes logic for querying `nvidia-smi` and database statistics within `ChatManager` to reuse HTTP client and database connection logic.
3.  **Bot `messages.py` handlers**: Integrates new admin commands into the existing message handling router.
