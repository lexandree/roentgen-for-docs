# Quickstart: Multi Model Dispatcher

**Feature Branch**: `002-multi-model-dispatcher`  
**Date**: 2026-03-08

## Overview

This module introduces a state machine (FSM) to the Telegram Bot, allowing doctors to select where their medical images should be processed:
- **Local GTX 1060**: Fast, single-image analysis.
- **Colab/RunPod**: Batch processing for MRI/CT series (up to 20 images).

It also adds an `interaction_logs` table to the local SQLite database to track usage.

## Database Initialization

To prepare the database for the new analytics table, you must run the database initialization script again. This will create the `interaction_logs` table without dropping existing whitelists.

```bash
# On your local server
python src/api/scripts/init_db.py --init
```

## Environment Variables

No new environment variables are strictly required, as the Google Drive credentials and Whitelist ID were set up in the previous step. However, ensure `GOOGLE_DRIVE_CREDENTIALS_FILE_PATH` is correctly pointing to your JSON key for the new folder isolation feature to work during Colab routing.

## Usage Guide (For the Doctor)

1. **Single Image**:
   - Drag and drop a single X-ray into the chat.
   - The bot will reply with a dynamically generated inline keyboard based on available workers (e.g., `[ ⚡️ Local (Python) ]` or `[ ⚡️ C++ Server ]`).
   - Click the desired route to begin analysis.

2. **Batch / Series (MRI)**:
   - Drag and drop multiple images at once (as a Telegram Album).
   - Wait 5 seconds.
   - The bot will group them and offer a batch-specific menu.
   - Alternatively, type `/analyze` to manually start a batch upload session.

3. **Cancellation**:
   - If you start a batch upload but change your mind, type `/clear` or send a new single image to automatically cancel the pending batch. Any files already staged on Google Drive will be automatically deleted from your isolated user folder.