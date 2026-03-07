# Feature Specification: Diagnostic Bot Core

**Feature Branch**: `001-diagnostic-bot-core`  
**Created**: 2026-03-07  
**Status**: Draft  
**Input**: User description: "Diagnostic bot core based on MedGemma 1.5. Designed for X-ray and MRI image analysis. Can start with text, but primary value is in image analysis followed by discussion."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Text-Based Medical Query (Priority: P1)

As a doctor, I want to send a text query to the Telegram bot to get general medical AI assistance or discuss a case without necessarily uploading an image first.

**Why this priority**: Lowering the barrier to entry allows doctors to use the bot immediately for general queries before committing to uploading sensitive medical images.

**Independent Test**: Can be tested by starting a new session and sending a purely text-based medical question. The bot must respond coherently using the MedGemma model.

**Acceptance Scenarios**:

1. **Given** the user has no active session, **When** they send a text query, **Then** the bot replies with the generated AI response and establishes an active text-based context.

---

### User Story 2 - Image-Based Diagnostic Analysis (Priority: P1)

As a doctor, I want to upload an X-ray or MRI image to the Telegram bot at any point in the conversation, so that MedGemma can analyze it and establish visual context for further discussion.

**Why this priority**: MedGemma 1.5's primary strength is image processing. This is the core differentiator of the tool.

**Independent Test**: Can be tested by uploading an image (either as the first message or mid-conversation). The bot must acknowledge the image, process it, and return a diagnostic report.

**Acceptance Scenarios**:

1. **Given** an active text session, **When** the user uploads a medical image, **Then** the bot analyzes the image, returns a diagnostic report, and sets the image as the new foundational context for the session.
2. **Given** no active session, **When** the user uploads a medical image as their first message, **Then** the bot analyzes it, returns the report, and starts a new session with that image as the context.

---

### User Story 3 - Handling Connectivity & Privacy (Priority: P2)

As a doctor, I want my sessions to be completely isolated from others, and I want clear error messages if the local MedGemma server is slow or unreachable, so I can trust the system's reliability and security.

**Why this priority**: Patient privacy is paramount, and network connections to local servers can drop.

**Independent Test**: Test isolation by having two users send queries simultaneously. Test connectivity by severing the Oracle-to-Local tunnel during an active discussion.

**Acceptance Scenarios**:

1. **Given** User A is discussing a case, **When** User B sends a query, **Then** User B's response does not cross-contaminate User A's session.
2. **Given** the local server drops offline during an active discussion, **When** the user asks a follow-up question, **Then** the bot replies with a clear timeout/error message within 30 seconds.

---

## Clarifications

### Session 2026-03-07
- Q: Can any Telegram user access the bot? → A: Strict whitelist (only pre-approved Telegram IDs).
- Q: What is the preferred mechanism for establishes this secure "bridge"? → A: Reverse SSH Tunnel (free, no certs/subscriptions required).

---

### Edge Cases

- What happens when a user uploads an unsupported file format (e.g., PDF, Word document, video)?
- What happens if the uploaded image is too large for Telegram's limits or the local API's payload limits?
- How does the system handle a user sending multiple images in a single batch (album)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST receive and parse both text messages and image files (e.g., JPEG, PNG) from users via Telegram.
- **FR-002**: The system MUST allow users to initiate and maintain a conversation using only text queries.
- **FR-003**: The system MUST allow users to upload an image at any time to add visual context to the current session or start a new one.
- **FR-004**: The system MUST securely forward both images and text queries from the Oracle cloud server to the local MedGemma server via a Reverse SSH Tunnel.
- **FR-005**: The local system MUST process the inputs using MedGemma 1.5 and generate a text response based on the combined history (text and/or image).
- **FR-006**: The system MUST notify the user if the local server is unreachable or if processing times out (within 30 seconds).
- **FR-007**: The system MUST maintain separate, isolated processing contexts for each unique Telegram user ID.
- **FR-008**: The system MUST automatically clear a user's context (including discussion history and KV-cache/session data) after 24 hours of inactivity. The raw physical image files MUST be deleted from the local disk immediately after being processed into visual embeddings by the model. Users MUST also be able to clear their session manually via a command (e.g., `/clear`).
- **FR-009**: The bot MUST fetch a whitelist of Telegram User IDs from a remote source (e.g., Google Drive) on startup and via a refresh command, rejecting unauthorized traffic before forwarding it. The local backend MUST also independently verify the whitelist.

### Constitution Requirements

- **CR-001**: Feature MUST strictly avoid persistently logging or saving sensitive medical data (images or discussion history) on the external Oracle server (Principle I).
- **CR-002**: Feature MUST implement graceful error handling for network timeouts during heavy inference (Principle III).
- **CR-003**: Feature MUST securely manage and isolate user context (Principle IV).

### Key Entities *(include if feature involves data)*

- **User Session**: Represents the isolated context for a specific doctor, keyed by their unique Telegram User ID. Contains the discussion history and any currently active medical image.
- **Medical Image**: Represents the optional X-ray or MRI visual payload that can act as context for the session.
- **Query/Response**: Represents the iterative text discussion between the doctor and the AI.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users successfully receive coherent responses for 99% of valid text and image interactions when the local server is online.
- **SC-002**: In the event of a local server disconnection, users receive a clear error notification 100% of the time.
- **SC-003**: Zero incidents of images, reports, or discussion context bleeding between different users' sessions.
- **SC-004**: All images and text queries temporarily held on the Oracle server during transit are securely deleted immediately after forwarding to the local server.
- **SC-005**: 100% of unauthorized access attempts are blocked at the cloud level without forwarding any data to the local server.