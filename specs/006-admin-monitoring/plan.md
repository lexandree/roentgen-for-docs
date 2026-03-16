# Implementation Plan: Integrated Admin Monitoring

**Branch**: `006-admin-monitoring` | **Date**: 2026-03-16 | **Spec**: [link to spec.md]
**Input**: Feature specification from `/specs/006-admin-monitoring/spec.md`

## Summary

Implement a suite of administrative commands within the existing Telegram bot to provide real-time business metrics, user activity data (for potential monetization), and basic application health. This replaces the initial idea of hardware-level monitoring (VRAM, CPU), delegating infrastructure monitoring to standard cloud tools, and focuses the bot purely on application-level insights.

## Technical Context

**Language/Version**: Python 3.12+ (FastAPI dispatcher, Aiogram bot)
**Primary Dependencies**: `httpx`, `aiosqlite`
**Target Platform**: Linux servers (Cloud for bot/dispatcher).
**Project Type**: Web-service (Dispatcher API & Telegram Bot)
**Constraints**: 
- Application health checks should be lightweight (e.g., HTTP ping to `/health` or `/props` of inference nodes).
- Database queries must efficiently aggregate metrics for session duration and usage limits without locking.
- Maintain low latency for admin commands.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Does it ensure patient data confidentiality? (Principle I: Security First) - *Only aggregated/admin-level data (request counts, session times), no raw patient info.*
- [x] Are Telegram handlers, API logic, and inference separated? (Principle II: Modularity) - *New admin API routes, new bot handlers. No hardware logic inside the dispatcher.*
- [x] Is graceful error handling implemented for network timeouts? (Principle III: Robustness) - *Worker health checks must gracefully handle timeouts.*
- [x] Is user context isolated? (Principle IV: Privacy) - *Admin access strictly enforced via whitelist.*
- [x] Is the Telegram bot acting as a lightweight relay? (Principle VI: Stateless/Stateful Design) - *Bot remains a relay; DB aggregations and health pings are in the API.*

## Project Structure

### Documentation (this feature)

```text
specs/006-admin-monitoring/
├── plan.md              
├── spec.md        
└── tasks.md             
```

### Source Code

```text
src/
├── api/
│   ├── routes/
│   │   └── admin.py      # NEW: Endpoints for admin queries (stats, business metrics, health ping)
│   └── services/
│       └── chat_manager.py # NEW: DB aggregations (session length) & worker ping logic
└── bot/
    └── handlers/
        └── messages.py   # NEW: Handlers for /admin_status, /admin_stats, /admin_user_stats
```

**Structure Decisions**:
1.  **New `admin.py` route file:** Isolates admin-specific API endpoints from general chat routing.
2.  **`ChatManager` for analytics & ping**: Handles the HTTP requests to worker health endpoints and performs SQL aggregations for user sessions.
3.  **Bot `messages.py` handlers**: Integrates new admin commands into the existing message handling router.
