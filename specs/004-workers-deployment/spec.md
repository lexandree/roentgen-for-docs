# Feature Specification: Workers and Deployment

**Feature Branch**: `004-workers-deployment`  
**Created**: 2026-03-10  
**Status**: Draft  

## User Scenarios & Testing

### User Story 1 - Standardized Worker Interface (Priority: P1)

As a developer, I want all inference workers (local, cloud, Colab, RunPod) to communicate via a standardized API contract, so the Dispatcher API doesn't need to know the implementation details of each worker.

**Why this priority**: It is the foundation for supporting multiple concurrent workers and platforms without tightly coupling the API to specific hardware or hosting providers.

**Independent Test**: Send a request to any mock worker adhering to the `/infer` or OpenAI `/v1/chat/completions` endpoint and receive a correctly formatted response.

**Acceptance Scenarios**:

1. **Given** an image and a text prompt, **When** the Dispatcher sends them to a standard worker adapter, **Then** the worker successfully unpacks the Base64 image, runs inference, and returns a JSON report.

---

### User Story 2 - Google Drive Adapter for Cloud Workers (Priority: P2)

As a cloud-hosted worker (like a Colab notebook), I want to download batches of images from a specific Google Drive folder and upload the results back, since I cannot maintain a persistent direct connection with the Dispatcher.

**Why this priority**: Essential for offloading heavy batch inference to ephemeral, free, or low-cost cloud GPUs (Kaggle/Colab).

**Independent Test**: Start a cloud worker adapter script, ensure it detects a pending batch in Google Drive, processes it, and uploads the `.json` results back to the same folder.

**Acceptance Scenarios**:

1. **Given** a user uploads a batch to `/batch`, **When** the Colab worker polls Google Drive, **Then** it finds the folder, downloads the images, runs MedGemma, saves the report, and updates the folder status.

---

### User Story 3 - Dockerized Deployment (Priority: P3)

As a system administrator, I want to deploy the Dispatcher API and Telegram Bot using Docker and Docker Compose so that I don't have to manage manual Python environments on my Oracle Cloud server.

**Why this priority**: Vastly simplifies server setup, ensuring environments match development and making updates trivial.

**Independent Test**: Run `docker-compose up -d` on a fresh machine with a `.env` file and observe both `api` and `bot` containers starting successfully and handling a `/start` command in Telegram.

**Acceptance Scenarios**:

1. **Given** a server with Docker installed, **When** executing `docker-compose build` and `up`, **Then** the SQLite database is initialized in a mounted volume, and both services start without errors.

## Requirements

### Functional Requirements

- **FR-001**: System MUST define a clear REST contract for custom Python workers (expecting Base64 images and returning `{"report": "..."}`).
- **FR-002**: System MUST include a standalone Python script `src/workers/cloud_adapter.py` that can poll Google Drive for batches, run inference, and save results.
- **FR-003**: System MUST provide a `Dockerfile` for the `api` service.
- **FR-004**: System MUST provide a `Dockerfile` for the `bot` service.
- **FR-005**: System MUST provide a `docker-compose.yml` that orchestrates `api` and `bot`, exposing necessary ports and mounting the `local_data.db` SQLite database as a persistent volume.
- **FR-006**: System MUST securely pass `.env` credentials to Docker containers.

### Constitution Requirements

- **CR-001**: Feature MUST NOT log sensitive medical images or data during Docker orchestration (Principle I: Security First).
- **CR-002**: Cloud worker adapters MUST strictly isolate Google Drive access by user ID (Principle IV).

### Key Entities

- **Worker Adapter**: A bridge between the Dispatcher's HTTP requests or Google Drive storage and the actual GPU running the LLM.
- **Docker Compose**: Orchestrates the API (port 8000) and Bot services.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Docker Compose successfully spins up the full application stack in under 5 minutes on a fresh host.
- **SC-002**: A Colab worker can successfully process a 5-image batch via the Google Drive adapter without manual intervention.