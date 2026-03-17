# Interface Contracts: Multi Model Dispatcher

**Feature Branch**: `002-multi-model-dispatcher`  
**Date**: 2026-03-08

## FastAPI Endpoints Update

The existing backend endpoints must be adapted to accept routing parameters and handle batch processing state management.

### `POST /api/v1/chat/message` (Updated)
Handles standard chat and single-image analysis requests.

**Request Body (FormData):**
- `telegram_id`: int
- `text`: str (Optional)
- `image`: UploadFile (Optional)
- `route`: str (Optional, Default: 'local') - Determines which model/infrastructure to use.

**Response (JSON):**
```json
{
  "status": "success",
  "data": {
    "response": "Analysis result string",
    "log_id": 123
  }
}
```

### `POST /api/v1/chat/batch` (New)
Handles the submission of a completed batch session (e.g., Colab or RunPod).

**Request Body (FormData):**
- `telegram_id`: int
- `text`: str (Optional, consolidated caption from the batch)
- `images`: List[UploadFile]
- `route`: str (Required, e.g., 'colab', 'runpod')

**Response (JSON):**
```json
{
  "status": "queued",
  "data": {
    "message": "Batch accepted and routed to colab.",
    "log_id": 124,
    "images_count": 5
  }
}
```

### `DELETE /api/v1/chat/batch` (New)
Cancels an active batch and deletes associated user folders from Google Drive.

**Request Body (JSON):**
```json
{
  "telegram_id": 123456789
}
```

**Response (JSON):**
```json
{
  "status": "success",
  "data": {
    "message": "Batch cancelled and files cleaned up."
  }
}
```