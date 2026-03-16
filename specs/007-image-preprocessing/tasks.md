# Implementation Tasks: ROI Image Preprocessing

**Branch**: `007-image-preprocessing` | **Date**: 2026-03-16 | **Spec**: [link to spec.md]

## 1. Backend - Image Processor Service

- **Goal**: Create a robust Pillow-based service for cropping images into squares to prevent aspect ratio distortion by the `llama-server`.
- **Tasks**:
  - [ ] Add `Pillow` to `src/api/requirements-dispatcher.txt` (if not already present).
  - [ ] Create `src/api/services/image_processor.py`.
  - [ ] Implement `process_main_image(image_bytes: bytes) -> bytes`:
    - Open with PIL.
    - Calculate the shortest side.
    - Perform a center crop to make it a perfect square.
    - Resize to 896x896 using `LANCZOS`.
    - Return as JPEG bytes.
  - [ ] Implement `process_roi_image(image_bytes: bytes, preset: str) -> bytes`:
    - Map presets (`top_left`, `top_right`, `bottom_left`, `bottom_right`, `center`) to coordinate centers.
    - Calculate a bounding box for a square crop centered on that logical region. The box size should be roughly 50% of the shortest side of the original image to ensure high zoom.
    - Ensure bounding box doesn't go outside image boundaries.
    - Crop, resize to 896x896, and return as JPEG bytes.

## 2. API - Route and Chat Manager Updates

- **Goal**: Allow the API to receive the ROI preset and process the images before dispatching to the worker.
- **Tasks**:
  - [ ] Update `POST /api/v1/chat/message` in `src/api/routes/chat.py` to accept an optional `roi_preset: Annotated[str | None, Form()] = None`.
  - [ ] In `chat.py`, if `roi_preset` is provided and exactly 1 image is uploaded:
    - Pass the image bytes to `image_processor`.
    - Generate `main_b64` and `roi_b64`.
    - Append BOTH images to `current_content` instead of just one.
    - Automatically append a text explanation: `"[System: Image 1 is the full overview. Image 2 is a zoomed-in detail of the {roi_preset.replace('_', ' ')}.]"` to the user's prompt.
  - [ ] If `roi_preset` is NOT provided (or for batch uploads), still process images through `process_main_image` to ensure they are squares and avoid distortion.

## 3. Bot - ROI Selection UI

- **Goal**: Present the user with a choice of regions when they upload a single image.
- **Tasks**:
  - [ ] Update `handle_document` in `src/bot/handlers/images.py`.
  - [ ] When a single image is uploaded (not an album), instead of immediately asking for the route, ask for the ROI.
  - [ ] Create `get_roi_keyboard()` returning Inline Buttons:
    - "🔍 Analyze Full Image" (callback: `roi_none`)
    - "↖️ Top Left" (`roi_top_left`)
    - "↗️ Top Right" (`roi_top_right`)
    - "⏺ Center" (`roi_center`)
    - "↙️ Bottom Left" (`roi_bottom_left`)
    - "↘️ Bottom Right" (`roi_bottom_right`)
  - [ ] Create a new FSM State `AnalysisSession.waiting_for_roi`.
  - [ ] Add a callback handler for `roi_*`.
    - Save the selected ROI to the FSM state data.
    - Transition to `waiting_for_route`.
    - Present the standard `get_dynamic_keyboard()` for worker selection.
  - [ ] Update `process_route_selection` in `src/bot/handlers/images.py` to retrieve `roi` from state data.
  - [ ] Update `api_client.send_message` to accept an optional `roi_preset: str = None` and pass it in the form data to the API.
