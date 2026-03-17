# Interface Contract: Local Inference API

This contract defines the REST API exposed by the local MedGemma server. The Telegram bot (running on Oracle Cloud) acts as a client to this API.

**Base URL**: `http://127.0.0.1:8000/api/v1` (Accessible via Reverse SSH Tunnel)

## Endpoints

### 1. Process Message
**POST** `/chat/message`

Sends a text message, an image, or both to the local server for processing. The local server handles authorization (whitelist), session management, and inference.

**Request (multipart/form-data):**
- `telegram_id` (integer, required): The Telegram ID of the sender.
- `text` (string, optional): The text query from the user.
- `image` (file, optional): The medical image file (JPEG/PNG).

*Note: Either `text` or `image` must be provided. If neither is provided, the request is invalid.*

**Response (200 OK):**
```json
{
  "status": "success",
  "response": "The generated diagnostic text from MedGemma based on the image and text context."
}
```

**Response (401 Unauthorized):**
```json
{
  "status": "error",
  "message": "User not in whitelist."
}
```

**Response (400 Bad Request):**
```json
{
  "status": "error",
  "message": "Invalid file format. Only JPEG/PNG supported."
}
```

### 2. Clear Session
**POST** `/chat/clear`

Manually clears the user's active session, conversation history, and local images.

**Request (JSON):**
```json
{
  "telegram_id": 123456789
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Session cleared successfully."
}
```