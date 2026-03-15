# Feature Specification: Integrated Admin Monitoring

**Feature Branch**: `008-admin-monitoring`  
**Created**: 2026-03-15  
**Status**: Draft  
**Input**: User description: "Integrated Admin Monitoring"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real-time Worker Health Status (Priority: P1)

As an administrator, I want to view the real-time health status of all inference workers, including their online/offline status, VRAM usage (for GPU workers), and current load, so that I can ensure the system is operational.

**Why this priority**: Immediate operational visibility is crucial for incident response and proactive system management.

**Independent Test**: Can be tested by running the command when workers are in various states (online, offline, sleeping, under load) and verifying the accuracy and completeness of the reported status.

**Acceptance Scenarios**:

1. **Given** I am an administrator, **When** I send the `/admin_status` command, **Then** I receive a summary of all configured workers including:
    - Worker ID and user-friendly name.
    - Current status (Online, Offline, Serverless, Timeout).
    - For local GPU workers, current VRAM usage (MiB).
    - For local CPU workers, approximate CPU load (%).
    - Timestamp of the status check.

---

### User Story 2 - System-Wide Usage Statistics (Priority: P2)

As an administrator, I want to view aggregated usage statistics (e.g., total requests, average response time, image count per worker) for a given period (daily/weekly/monthly), so that I can monitor system performance and resource consumption trends.

**Why this priority**: Provides insights into system load and helps with capacity planning and resource allocation.

**Independent Test**: Can be tested by making several requests over a period and then querying the statistics, verifying that the aggregated data correctly reflects the activity.

**Acceptance Scenarios**:

1. **Given** I am an administrator, **When** I send the `/admin_stats` command (optionally with a period like `daily`, `weekly`, `monthly`), **Then** I receive a summary including:
    - Total requests processed.
    - Average inference latency across all workers.
    - Total images processed.
    - Breakdown of requests per worker route.
    - Breakdown of requests by `task_type` (single image, batch).

---

### User Story 3 - Individual User Statistics (Priority: P3)

As an administrator, I want to view specific usage statistics for individual users, so that I can track activity and enforce policies (e.g., daily limits).

**Why this priority**: Essential for user management, auditing, and enforcing fair usage policies.

**Independent Test**: Can be tested by making several requests as a specific user and then querying their statistics, verifying that the data is correctly attributed and aggregated.

**Acceptance Scenarios**:

1. **Given** I am an administrator, **When** I send the `/admin_user_stats <telegram_id>` command, **Then** I receive a detailed report for that user, including:
    - Total requests.
    - Total images processed.
    - Average latency for their requests.
    - Last activity timestamp.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Implement a `/admin_status` command in the Telegram bot to display comprehensive worker health.
- **FR-002**: Implement a `/admin_stats` command in the Telegram bot to display system-wide usage statistics.
- **FR-003**: Implement a `/admin_user_stats [telegram_id]` command in the Telegram bot to display individual user statistics.
- **FR-004**: The `/admin_status` command MUST include GPU VRAM usage and CPU load for local workers.
- **FR-005**: All admin commands MUST be restricted to users with `"role": "admin"` in the whitelist.

### Constitution Requirements

- **CR-001**: Feature MUST strictly adhere to data privacy by only showing aggregated or admin-level user data, and never raw patient data (Principle I).
- **CR-002**: Feature MUST provide secure access control for admin commands (Principle IV).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admin can retrieve real-time worker health status within 5 seconds.
- **SC-002**: Admin can retrieve system-wide usage statistics within 10 seconds.
- **SC-003**: Admin can retrieve individual user statistics within 10 seconds.
