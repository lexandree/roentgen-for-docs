# Implementation Plan: ROI Image Preprocessing

**Branch**: `007-image-preprocessing` | **Date**: 2026-03-16 | **Spec**: [link to spec.md]

## Summary

Implement a text-based/button-based mechanism for users to select a Region of Interest (ROI) on a single uploaded medical image before sending it to the MedGemma inference worker. This feature addresses the limitation of the `llama-server` forcing all images into a square 896x896 aspect ratio, which distorts rectangular x-rays.

## Technical Context

**Language/Version**: Python 3.12+ (FastAPI dispatcher, Aiogram bot)
**Primary Dependencies**: `Pillow` (for image manipulation), `aiogram` (for bot UI), `httpx` (for internal API calls)
**Target Platform**: Linux servers (Cloud for bot/dispatcher).
**Project Type**: Web-service (Dispatcher API & Telegram Bot)
**Constraints**: 
- `llama-server` internally resizes to 896x896 without preserving aspect ratio. We must pre-process images into squares to prevent anatomical distortion.
- The workflow only applies to single-image uploads (not batches).

## Strategy: Two-Image Submission

When a user selects an ROI (e.g., "Top Right"):
1.  **Main Image Processing**: The original rectangular image is cropped into a **square** by centering on the overall image (to prevent the `llama-server` from squashing it horizontally).
2.  **ROI Image Processing**: The specified quadrant/region is mathematically calculated from the original high-resolution image. It is also cropped into a **square** centered on that region's logical center.
3.  **Inference**: Both the square Main Image and the square ROI Image are sent to the worker in a single prompt, accompanied by an automatic contextual prompt (e.g., "Image 1 is the full view. Image 2 is a detailed view of the Top Right quadrant.").

## Constitution Check

- [x] Does it ensure patient data confidentiality? (Principle I: Security First) - *Image processing happens entirely in memory on our trusted Dispatcher server.*
- [x] Are Telegram handlers, API logic, and inference separated? (Principle II: Modularity) - *Bot handles the UI (Inline buttons), API handles the Pillow image cropping.*
- [x] Is the Telegram bot acting as a lightweight relay? (Principle VI: Stateless/Stateful Design) - *Yes, bot just sends the ROI command to the API.*

## Project Structure

```text
src/
├── api/
│   ├── services/
│   │   ├── image_processor.py  # NEW: Pillow logic for square crops and ROI extraction
│   │   └── chat_manager.py     # UPDATED: To call image_processor before sending to worker
│   └── routes/
│       └── chat.py             # UPDATED: To accept an optional 'roi_preset' parameter
└── bot/
    ├── handlers/
    │   └── images.py           # UPDATED: Add InlineKeyboard for ROI selection on single images
    └── services/
        └── api_client.py       # UPDATED: Pass 'roi_preset' to the API
```

## Step-by-Step Plan

1.  **Backend Image Processor (`src/api/services/image_processor.py`)**:
    *   Create a class to handle `Pillow` operations.
    *   Implement `make_square(image: bytes)`: Crops a rectangular image into a square (center crop) and resizes to 896x896.
    *   Implement `extract_roi(image: bytes, preset: str)`: Maps presets (`top_left`, `bottom_right`, `center`, etc.) to coordinates, crops a square around that center, and resizes to 896x896.
2.  **API Integration (`src/api/routes/chat.py` & `chat_manager.py`)**:
    *   Update `/chat/message` to accept an optional `roi_preset` form field.
    *   If `roi_preset` is provided, use `image_processor` to generate two image bytes objects (Main Square + ROI Square) from the single uploaded file.
    *   Inject an automatic text prompt explaining the two images to the model.
3.  **Bot UI (`src/bot/handlers/images.py`)**:
    *   When a user uploads a *single* uncompressed image, instead of immediately processing it, present an InlineKeyboard with options: "Analyze Full Image" and various ROI quadrants (Top Left, Top Right, Bottom Left, Bottom Right, Center).
    *   Handle the callback query. If an ROI is selected, pass that preset to `api_client.send_message`.
