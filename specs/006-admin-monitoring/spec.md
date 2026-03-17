# Feature Specification: Integrated Admin Monitoring

**Feature Branch**: `006-admin-monitoring`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Integrated Admin Monitoring with focus on business metrics and session duration"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Application Health Status (Priority: P1)

As an administrator, I want to view the real-time health status of all inference workers via a lightweight network ping, so that I can ensure the backend services (e.g., `llama-server`) are responsive.

**Why this priority**: Immediate visibility into application uptime is crucial for incident response, without reinventing hardware monitoring.

**Acceptance Scenarios**:

1. **Given** I am an administrator, **When** I send the `/admin_status` command, **Then** I receive a summary of all configured workers including:
    - Worker URL / identifier.
    - Current status (Online / Offline / Timeout).
    - Response latency (ping time).
    - Timestamp of the status check.

---

### User Story 2 - System-Wide Business Statistics (Priority: P2)

As an administrator, I want to view aggregated usage statistics (total requests, average response time, image count) for a given period, so that I can monitor business performance and system load.

**Why this priority**: Provides insights into system adoption and helps with capacity planning.

**Acceptance Scenarios**:

1. **Given** I am an administrator, **When** I send the `/admin_stats` command (optionally with a period like `daily`, `weekly`, `monthly`), **Then** I receive a summary including:
    - Total requests processed.
    - Average inference latency across all workers.
    - Total images processed.
    - Breakdown of requests per worker route.

---

### User Story 3 - User Activity & Monetization Metrics (Priority: P1)

As an administrator, I want to view specific usage statistics for individual users, including their session duration and request volume, so that I can track activity for potential monetization (service on-demand) and enforce usage policies.

**Why this priority**: Crucial for tracking how long users engage with the service, which is a key metric for on-demand billing or quota management.

**Acceptance Scenarios**:

1. **Given** I am an administrator, **When** I send the `/admin_user_stats <telegram_id>` command, **Then** I receive a detailed report for that user, including:
    - Total requests and images processed.
    - **Total active session duration** (calculated based on time between first and last interaction within contiguous blocks of activity).
    - Average latency for their requests.
    - Last activity timestamp.

---

### User Story 4 - Worker Usage & Cost Metrics (Priority: P2)

As an administrator, I want to view usage statistics grouped by inference worker (route), including token usage, so that I can estimate cloud provider costs.

**Why this priority**: Cloud GPUs are billed either by time or by token. Tracking tokens and request volume per worker helps in reconciling bills and optimizing routing.

**Acceptance Scenarios**:

1. **Given** I am an administrator, **When** I send the `/admin_worker_stats` command (optionally with a period like `daily`, `weekly`, `monthly`), **Then** I receive a summary including:
    - Breakdown per worker (route).
    - Total requests for that worker.
    - Total input and output tokens for that worker.
    - Total images processed by that worker.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Implement a `/admin_status` command in the Telegram bot to display worker application health (ping/latency).
- **FR-002**: Implement a `/admin_stats` command in the Telegram bot to display system-wide usage statistics.
- **FR-003**: Implement a `/admin_user_stats [telegram_id]` command in the Telegram bot to display individual user statistics, prominently featuring **session duration** metrics.
- **FR-004**: Health checks MUST NOT rely on local system commands (`nvidia-smi`, `top`), but rather on HTTP requests to the worker's API (e.g., `/health`).
- **FR-005**: All admin commands MUST be restricted to users with `"role": "admin"` in the whitelist.
- **FR-006**: Implement `/admin_worker_stats` command to display usage statistics and token counts grouped by worker route.

### Constitution Requirements

- **CR-001**: Feature MUST strictly adhere to data privacy by only showing aggregated or admin-level user data, and never raw patient data (Principle I).
- **CR-002**: Feature MUST provide secure access control for admin commands (Principle IV).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admin can retrieve real-time worker application health within 5 seconds.
- **SC-002**: Admin can retrieve system-wide usage statistics within 10 seconds.
- **SC-003**: Admin can retrieve individual user statistics (including session duration) within 10 seconds.
- **SC-004**: Admin can retrieve worker usage statistics (including tokens) within 10 seconds.
