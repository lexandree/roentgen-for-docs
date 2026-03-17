# Implementation Plan: Workers and Deployment

## Approach
1.  **Standardize Worker Contracts**:
    - Review and refine the `src/api/worker.py` (Custom Python Worker) to ensure it handles incoming multimodal messages correctly.
    - Ensure the Dispatcher API (`src/api/routes/chat.py`) consistently sends standardized payloads.
2.  **Cloud Worker Adapter (`src/workers/cloud_adapter.py`)**:
    - Implement a polling service designed to run on Colab/Kaggle.
    - It will use `google-api-python-client` to watch for folders in the `GDRIVE_BATCH_FOLDER_ID`.
    - Workflow: Detect new user folder -> Download images -> Run local inference -> Write `report.json` -> Update folder status.
3.  **Dockerization**:
    - Create `src/api/Dockerfile` using a Python 3.12 slim base image. Install dependencies from `src/api/requirements.txt`.
    - Create `src/bot/Dockerfile` using a Python 3.12 slim base image. Install dependencies from `src/bot/requirements.txt`.
    - Create a root `docker-compose.yml` to orchestrate both services, mounting `local_data.db` and passing `.env` variables.
4.  **Security & Environment**:
    - Use Docker secret/environment injection for sensitive keys (GDrive credentials).
    - Ensure SQLite database persistence through volume mapping.

## Scope & Constraints
- Dockerization focuses on the **Dispatcher** (Oracle Cloud) components.
- GPU-heavy workers (local or cloud) will likely remain as standalone Python environments due to complex CUDA/Driver dependencies, but they will communicate via the standardized web/GDrive interface.

## Dependencies
- Docker & Docker Compose on the host machine.
- `google-api-python-client` (already used in shared services).
