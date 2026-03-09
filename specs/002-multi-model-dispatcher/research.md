# Research: Multi Model Dispatcher

**Feature Branch**: `002-multi-model-dispatcher`  
**Date**: 2026-03-08

## Topic: aiogram 3.x Media Group Handling & FSM (5-second window)
- **Decision**: Use a combination of `aiogram`'s `FSMContext` (with an `AnalysisSession` state group) and an `asyncio.sleep` task or `Cache` to debounce media group items, accumulating them until 5 seconds have passed without new items. 
- **Rationale**: Telegram sends albums as individual messages sharing the same `media_group_id`. To process them as a batch and show only one menu, we must "wait" for the burst to finish. Using an asyncio task that is refreshed/cancelled on each new item in the group is a standard, non-blocking pattern in `aiogram` 3.
- **Alternatives considered**: Middlewares (too complex for a simple state machine), database tracking (too slow, excessive writes for a 5-second window).

## Topic: Database Structure for interaction_logs (SQLite + aiosqlite)
- **Decision**: Create an `interaction_logs` table via `init_db.py` (using raw SQL execution with `aiosqlite` as currently implemented) holding fields like `telegram_id`, `route`, `task_type`, `images_count`, `status`, `created_at`, `completed_at`.
- **Rationale**: Fits perfectly with the existing lightweight `sqlite+aiosqlite` setup. No heavy ORM required since the schema is simple and performance needs are low (single-user bot currently, minimal concurrent DB writes).
- **Alternatives considered**: SQLAlchemy/Tortoise ORM (overkill for the current scope).

## Topic: Google Drive Isolated Folders
- **Decision**: Use `google-api-python-client` with the existing Service Account credentials. Create a subfolder under a root 'MedGemma Batches' folder named with the `telegram_id`. Store batch images there. On batch cancellation, query for this specific folder ID and issue a `files().delete()` call.
- **Rationale**: Direct integration with the API allows clean separation of context (Principle IV). Deleting the folder atomically guarantees no residual medical data is left behind.
- **Alternatives considered**: Storing all images in a flat structure with prefixes (harder to delete atomically, messy).

## Topic: Local Model Inference Engine (llama.cpp vs KoboldCPP)
- **Decision**: Use `llama-cpp-python` directly integrated into the FastAPI backend instead of a standalone `KoboldCPP` server.
- **Rationale**: While `KoboldCPP` is excellent for out-of-the-box GUI-based inference, integrating `llama-cpp-python` directly gives us full programmatic control over memory, lifecycle, and API endpoints within our existing FastAPI structure. This allows us to handle image processing (`Pillow`), Base64 conversions, and custom prompting logic directly inside our worker, without adding the overhead of maintaining and proxying requests to a secondary web server.
- **Alternatives considered**: `KoboldCPP` (rejected due to added complexity of managing a separate server process), `transformers` with `accelerate` (rejected due to higher VRAM usage on GTX 1060).

## Topic: Cloud Hosting, Workers, and Privacy Dynamics
- **Decision**: The architecture must support a flexible "worker" model where external compute nodes can be connected. While strict privacy (local inference only) is the default, the user has consciously chosen to allow routing to arbitrary external workers for heavy tasks. Specifically, the system supports:
  1. **RunPod**: For renting specific GPUs suitable for the workload.
  2. **Google Colab (Interactive/Hacker)**: Running a Jupyter notebook interactively.
  3. **Google Colab (Batch/Background)**: Using Colab as an asynchronous batch processor.
- **Rationale**: The user's workflow requires processing capabilities beyond what a local GTX 1060 can provide. By decoupling the API from the inference worker, the user takes responsibility for the privacy implications of sending data to RunPod or Google Colab. The system's job is to ensure the routing is secure and the data is cleaned up (e.g., via Google Drive isolation) when the session ends, adapting the "Security First" principle to a Bring-Your-Own-Compute (BYOC) model.

## Topic: Worker Abstraction and GDrive Permission Scoping
- **Decision**: Implement a strict "Worker Adapter" pattern for Colab to keep the FastAPI Dispatcher agnostic. The responsibilities and permissions are strictly isolated:
  1. **Dispatcher**: Knows *nothing* about file storage for workers. It only sends HTTP requests (images + text) to a standard worker endpoint. Its Google Drive access is strictly **READ-ONLY** and limited to a single file (`whitelist.txt`).
  2. **Colab Worker Adapter**: A separate local service/module that receives the standard HTTP request from the Dispatcher. It has **FULL ACCESS** to the dedicated Google Drive batches folder. It handles uploading images, polling/waiting for the notebook, and cleaning up the folder afterward.
  3. **Colab Notebook**: Has **READ/WRITE** access *only* to the specific shared Drive folder to download images, perform inference, and write back the results (or trigger a webhook to the Adapter).
- **Rationale**: This enforces the Principle of Least Privilege and the Single Responsibility Principle. By not mixing the Dispatcher's whitelist reading logic with the Worker's file-based IPC logic, we avoid over-engineering the Dispatcher. If the Colab storage mechanism changes in the future, the Dispatcher remains untouched.