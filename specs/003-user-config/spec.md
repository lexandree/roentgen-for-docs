# Feature Specification: Convert whitelist to JSON user configs

**Feature Branch**: `003-003-user-config`  
**Created**: 2026-03-10  
**Status**: Draft  

## User Scenarios & Testing

### User Story 1 - JSON Whitelist Configs (Priority: P1)

As an administrator, I want to manage a JSON-based whitelist file in Google Drive so that I can configure individual permissions and parameters for each user.

**Why this priority**: Required to support distinct worker access permissions and admin roles per user.

**Independent Test**: Update Google Drive file to JSON format, invoke `/refresh_whitelist`, and observe updated user privileges in the database.

**Acceptance Scenarios**:

1. **Given** a JSON file containing `users` on Drive, **When** bot synchronizes whitelist, **Then** all user fields (role, allowed_workers, daily_limit, specialty, system_prompt_type, is_active) are correctly stored in the SQLite DB and cached.
2. **Given** a user with `is_active=false`, **When** the user sends a message, **Then** the bot rejects the request.

---

### User Story 2 - Granular Worker Access (Priority: P2)

As a system, I want to route requests to workers based on the `allowed_workers` list defined for the specific user.

**Why this priority**: Ensures that costly remote workers are only used by authorized doctors.

**Independent Test**: Send a request using a user account lacking permission to `colab_heavy` and verify it's rejected.

**Acceptance Scenarios**:

1. **Given** a user with `allowed_workers: ["local_python"]`, **When** they request `colab_heavy`, **Then** the API rejects the request with HTTP 403.

---

### User Story 3 - Role-Based Command Access (Priority: P3)

As a system administrator, I want exclusive access to sensitive bot commands like `/refresh_whitelist`.

**Why this priority**: Prevents unauthorized users from manipulating system-level caches.

**Independent Test**: Send `/refresh_whitelist` from a user lacking the `admin` role and observe rejection.

**Acceptance Scenarios**:

1. **Given** a user with `role: "user"`, **When** they invoke `/refresh_whitelist`, **Then** the bot ignores the command or replies with a permission denied message.

---

### User Story 4 - Dynamic System Prompts (Priority: P4)

As an administrator, I want to define different system prompts for different users directly in the Google Drive JSON file.

**Why this priority**: Allows easily switching model personas (e.g. strict radiologist vs helpful practitioner) without deploying code changes.

**Independent Test**: Update Google Drive JSON to include a `prompts` section, assign a `system_prompt_type` to a user, sync whitelist, and verify the correct prompt is passed to the worker.

**Acceptance Scenarios**:

1. **Given** a JSON file containing `prompts` and `users` mapping to those prompts, **When** a user sends a message, **Then** the system retrieves the specific prompt text from the DB and sends it to the inference worker.

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse the whitelist file from Google Drive as a JSON object containing nested user configs in a `users` object, and prompt configurations in a `prompts` object.
- **FR-002**: System MUST sync `name`, `system_prompt_type`, `role`, `allowed_workers`, `is_active`, `daily_limit`, and `specialty` to the local database and memory cache.
- **FR-003**: System MUST reject messages from users marked as `is_active: false`.
- **FR-004**: System MUST reject command `/refresh_whitelist` if `role` is not `admin`.
- **FR-005**: System MUST restrict inference request routing according to the user's `allowed_workers` configuration.
- **FR-006**: System MUST perform DB schema migration gracefully (e.g. `ALTER TABLE users ADD COLUMN...` with error handling if column exists) in `init_db`.
- **FR-007**: System MUST sync `system_prompts` data into a new database table and dynamically fetch the correct text during inference.

### Constitution Requirements

- **CR-001**: Feature MUST securely manage and isolate user context (Principle IV) when accessing authorized workers.

### Key Entities

- **User**: Now includes granular settings (`role`, `allowed_workers`, `specialty`, `system_prompt_type`, `daily_limit`).
- **SystemPrompt**: Stores dynamic AI behavior instructions (`id`, `description`, `content`).

## Success Criteria

### Measurable Outcomes

- **SC-001**: Whitelist fetched successfully in < 3 seconds from Drive.
- **SC-002**: 100% of inactive users are correctly blocked.
- **SC-003**: 100% of admin commands are restricted to users with `role: "admin"`.
- **SC-004**: System successfully applies different prompt instructions based on user profile.
