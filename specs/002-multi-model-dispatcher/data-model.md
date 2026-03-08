# Data Model: Multi Model Dispatcher

**Feature Branch**: `002-multi-model-dispatcher`  
**Date**: 2026-03-08

## Entities

### `InteractionLog` (Database Table)
Stores analytical data about medical image processing tasks for auditing and monitoring.

*   `id` (INTEGER, Primary Key, Auto-increment)
*   `telegram_id` (INTEGER, Not Null) - References the user making the request.
*   `route` (TEXT, Not Null) - Enum-like string (`local`, `colab`, `runpod`).
*   `task_type` (TEXT, Not Null) - Enum-like string (`single`, `batch`).
*   `images_count` (INTEGER, Not Null) - Number of images processed in this task.
*   `status` (TEXT, Not Null) - Current state of the task (`queued`, `processing`, `completed`, `failed`, `cancelled`).
*   `created_at` (TIMESTAMP, Default CURRENT_TIMESTAMP)
*   `completed_at` (TIMESTAMP, Nullable)

### `AnalysisSession` (FSM State)
Represents the transient state of a user's interaction while grouping images or choosing a route. Stored in MemoryStorage or Redis by `aiogram`.

*   `state` (String) - `waiting_for_route` or `waiting_for_batch_images`.
*   `data` (Dict):
    *   `route` (String, Optional) - The selected route.
    *   `images` (List[Dict]) - List of uploaded image metadata/bytes.
        *   `file_id` (String) - Telegram file ID.
        *   `caption` (String, Nullable) - Text provided with the image.
    *   `media_group_id` (String, Optional) - Identifier for an active album upload.

## Validation Rules & State Transitions

**AnalysisSession Constraints:**
- `images` list length MUST NOT exceed 20. If an attempt is made to append the 21st image, it is rejected with a warning.
- Transitioning to a new task MUST clear existing FSM data to prevent cross-contamination.

**InteractionLog Transitions:**
- Record created with `status = 'queued'` upon route confirmation.
- Status updates to `processing` when the backend accepts the payload.
- Status updates to `completed` or `failed` upon backend response or network timeout.
- `completed_at` is set when reaching a terminal state.