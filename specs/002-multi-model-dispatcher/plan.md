# Implementation Plan: Multi Model Dispatcher

**Branch**: `002-multi-model-dispatcher` | **Date**: 2026-03-08 | **Spec**: [specs/002-multi-model-dispatcher/spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-multi-model-dispatcher/spec.md`

## Summary

Implement an `aiogram` Finite State Machine (FSM) to handle dynamic routing of medical images to different AI backends (Local GTX 1060, Colab (Hacker/Interactive), Colab (Batch), RunPod) based on user selection. Introduce a 5-second debounce window to correctly group Telegram Albums into batches (up to 20 images) and store batch files in isolated Google Drive subdirectories for easy cleanup. Track all interactions via a new `interaction_logs` table in the local SQLite database.

## Technical Context

**Language/Version**: Python 3.12+
**Primary Dependencies**: `aiogram` (for FSM and Telegram handling), `FastAPI` (for routing endpoints), `aiosqlite` (for DB interaction logs), `google-api-python-client` (for Drive folder management)
**Storage**: SQLite (`local_data.db`), Google Drive (isolated user folders for Colab batches), MemoryStorage/Redis (for `aiogram` FSM)
**Testing**: `pytest`
**Target Platform**: Linux (Local Server + Oracle Cloud)
**Project Type**: Telegram Bot + FastAPI Service
**Performance Goals**: Fast local single-image inference; stable batch processing for up to 20 images on remote workers.
**Constraints**: Avoid OOM on 6GB GTX 1060; isolate Google Drive folders by `telegram_id` for cloud workers.
**Scale/Scope**: Medical practitioners (single to few users currently)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Does it ensure patient data confidentiality? (Principle I: Security First) - Yes, `interaction_logs` only stores metadata, not PHI. Batches sent to external workers (Colab, RunPod) are stored in isolated Google Drive folders and deleted on cancellation, adapting to a Bring-Your-Own-Compute privacy model.
- [x] Are Telegram handlers, API logic, and inference separated? (Principle II: Modularity) - Yes, the FSM is in the bot layer, while routing logic and logging are handled via FastAPI endpoints.
- [x] Is graceful error handling implemented for network timeouts? (Principle III: Robustness) - Yes, network errors will be logged in `interaction_logs` with a `failed` status, and users will be notified.
- [x] Is user context isolated? (Principle IV: Privacy) - Yes, FSM isolates state per `telegram_id`, and Drive folders are explicitly isolated by ID.
- [x] Is the Telegram bot acting as a lightweight relay? (Principle VI: Stateless/Stateful Design) - Yes, the FSM manages temporary state, but heavy data processing/persistence is offloaded to the backend and Google Drive.

## Project Structure

### Documentation (this feature)

```text
specs/002-multi-model-dispatcher/
├── plan.md              
├── research.md          
├── data-model.md        
├── quickstart.md        
├── contracts/           
│   └── local-inference-api.md
└── tasks.md             # (To be generated in Phase 2)
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── db/
│   │   ├── database.py       # Update schema creation logic
│   │   └── models.py         # Add interaction_logs queries/structures
│   ├── routes/
│   │   └── chat.py           # Add generic routing and batch endpoints (GDrive logic removed)
│   ├── scripts/
│   │   └── init_db.py        # Ensure interaction_logs table is created
│   └── services/
│       └── inference.py      # Abstract inference routing
├── bot/
│   ├── handlers/
│   │   ├── images.py         # Add FSM logic and 5-second debounce window
│   │   └── messages.py       # Add /analyze command and FSM callbacks
│   └── services/
│       └── api_client.py     # Update to call new batch/routing API endpoints
├── workers/                  # NEW: External Worker Adapters
│   └── colab/
│       ├── main.py           # FastAPI app for the Colab Worker Adapter
│       └── gdrive_ipc.py     # Logic for uploading to GDrive and polling/webhooks
└── shared/
    └── services/
        └── gdrive_whitelist.py # Dispatcher's Read-Only Whitelist service
```

**Structure Decision**: Expanding the architecture to include a `workers/colab/` module. This enforces the Worker Abstraction pattern, ensuring the core `api` (Dispatcher) remains agnostic to Colab-specific Google Drive operations.