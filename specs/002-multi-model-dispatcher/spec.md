# Feature Specification: Multi Model Dispatcher

**Feature Branch**: `002-multi-model-dispatcher`  
**Created**: 2026-03-08
**Status**: Draft  
**Input**: User description: "002-multi-model-dispatcher согласно обсужденному" (Implementing FSM and Routing for Local 1060, Colab, and RunPod with Interaction Logs).

## Clarifications
### Session 2026-03-08
- Q: How long should the bot wait to group images sent as a Telegram Album before presenting the batch routing menu? → A: 5 seconds
- Q: What is the maximum number of images allowed in a single batch analysis? → A: 20 images
- Q: If a user sends a single image, receives the routing menu, but sends another single image before selecting a route for the first, how should the bot handle the second image? → A: Cancel first, process new
- Q: How should batch images be stored on Google Drive to allow for easy cancellation or isolation? → A: Files must be stored in subdirectories named after the user's `telegram_id` so the entire batch can be cleanly deleted if the user cancels the operation.
- Q: How do we handle authentication for external workers (RunPod, Colab) since they are exposed to the public internet? → A: The system must support passing Bearer tokens or API keys defined in the environment variables when dispatching requests to external worker URLs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Quick Analysis (Single Image) (Priority: P1)

As a doctor, I want to quickly analyze a single medical image (e.g., X-ray) using my local server so that I get an immediate response without unnecessary clicks.

**Why this priority**: Single-image analysis is the most frequent use case and should be the path of least resistance.

**Independent Test**: Send a single photo with an optional text caption. The bot should immediately offer routing options including the fast local server. Selecting it should process the image and return the result.

**Acceptance Scenarios**:

1. **Given** the bot is waiting for input, **When** the user sends a single photo with or without text, **Then** the bot replies with an inline keyboard to choose the routing destination (e.g., Local GTX 1060, Colab).
2. **Given** the routing menu is displayed, **When** the user selects the local route, **Then** the bot updates its status to "Processing", sends the data to the local server, and returns the response.

---

### User Story 2 - Batch/Series Analysis (Multiple Images) (Priority: P2)

As a doctor, I want to upload a series of images (e.g., MRI slices) or an album and process them together using a powerful remote server (Colab or RunPod) so that I can evaluate changes over time or complex 3D structures.

**Why this priority**: MRI and CT scans are fundamental to diagnostics, and they always consist of multiple images requiring significant VRAM.

**Independent Test**: Use the `/analyze` command to enter a specific "waiting for images" state, upload multiple images, and then dispatch them to a heavy-duty route. Alternatively, send an album (Media Group) directly and receive a batch routing menu.

**Acceptance Scenarios**:

1. **Given** the bot is waiting for input, **When** the user sends an album of images (Media Group), **Then** the bot groups them and presents a routing menu specifically for batch processing (excluding the low-VRAM local option).
2. **Given** the user uses the `/analyze` command, **When** they select a heavy-duty route (e.g., Colab), **Then** the bot enters a state waiting for image uploads.
3. **Given** the bot is in the image upload state, **When** the user uploads multiple images and clicks "Finish", **Then** the entire batch is queued for processing on the selected route.
4. **Given** the bot is in the image upload state, **When** the user attempts to upload more than 20 images, **Then** the bot rejects the excess images and warns the user about the limit.

---

### User Story 3 - Usage Analytics and Monitoring (Priority: P3)

As an administrator, I want to log every interaction (user, chosen route, number of images, duration) so that I can monitor system load, track usage, and manage quotas (e.g., $10/month RunPod budget).

**Why this priority**: Essential for non-commercial projects to prevent abuse and manage limited resources effectively.

**Independent Test**: Complete any analysis task (User Story 1 or 2) and verify that a new record is created in the database containing the correct metadata.

**Acceptance Scenarios**:

1. **Given** a user initiates an analysis task, **When** the task completes (successfully or fails), **Then** the system logs the event in the `interaction_logs` table with start/end times, route used, and task type.

### Edge Cases

- What happens when a user sends a document instead of a compressed photo? (Should be rejected or handled appropriately if it's a valid medical format like DICOM - currently assuming standard image formats).
- How does the system handle a user starting a batch upload but never clicking "Finish"? (Needs a timeout or clear command to reset the state).
- What if the local server is offline when the user selects the local route? (Bot should return a friendly error and allow selecting a different route).
- What if a user sends a single image, gets the routing menu, and then sends another image before selecting a route? (The bot MUST cancel the active routing request for the first image, clear it from temporary memory, and present a new routing menu for the second image).
- What happens if a user cancels a batch analysis that was already uploaded to Google Drive? (The system must locate the user's specific folder based on their Telegram ID and delete the entire folder and its contents).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an inline keyboard for route selection after receiving a single image.
- **FR-002**: System MUST support a state machine (FSM) to handle batch uploads via a dedicated command (`/analyze`).
- **FR-003**: System MUST automatically group media sent as Telegram Albums (`media_group_id`), waiting 5 seconds before finalizing the group and presenting a batch-specific routing menu.
- **FR-004**: System MUST route requests to different inference endpoints (Local, Colab (Hacker/Interactive), Colab (Batch), RunPod) based on user selection.
- **FR-005**: System MUST log all analysis interactions in a database table, including user ID, route, image count, and timestamps.
- **FR-006**: System MUST hide or disable the "Local" route option if a batch of images is detected, as it exceeds local VRAM capacity.
- **FR-007**: System MUST allow text captions to accompany images and forward them to the selected model.
- **FR-008**: System MUST limit batch image uploads to a maximum of 20 images per session, displaying a clear error if the limit is exceeded.
- **FR-009**: System MUST store batch images uploaded to Google Drive (for Colab) in isolated subdirectories named after the user's Telegram ID to enable easy cancellation and cleanup.
- **FR-010**: System MUST support configuring authentication credentials (e.g., API keys, Bearer tokens) for remote workers like RunPod and Colab, appending them securely to outgoing inference requests.

### Constitution Requirements

- **CR-001**: Feature MUST strictly avoid logging sensitive medical data (images or diagnostic text) in the analytics database (Principle I).
- **CR-002**: Feature MUST implement graceful error handling for network timeouts when communicating with remote servers like RunPod or Colab (Principle III).
- **CR-003**: Feature MUST securely manage and isolate user context within the FSM so users cannot access each other's uploaded batches (Principle IV).

### Key Entities

- **InteractionLog**: Represents a single session. Attributes: ID, User ID (Telegram), Route (Local/Colab/RunPod), Task Type (Single/Batch), Images Count, Status, Start Time, End Time.
- **AnalysisSession (FSM State)**: Temporary state holding uploaded images and selected route before dispatching to the backend.
- **WorkerConfig**: Definition of external workers containing URLs and associated Authentication tokens.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of interactions are successfully logged in the database without containing patient health information (PHI).
- **SC-002**: Users can successfully route a single image to the local server in 2 clicks or fewer.
- **SC-003**: Users can successfully queue a batch of images for external processing without the bot crashing or losing images in the sequence.
- **SC-004**: System correctly groups Telegram Albums into a single batch request 100% of the time, rather than treating them as N separate requests.
- **SC-005**: External workers receive requests with correctly attached API keys/Bearer tokens, preventing unauthorized public access to inference nodes.