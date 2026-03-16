# Feature Specification: ROI Image Preprocessing

**Feature Branch**: `007-image-preprocessing`  
**Created**: 2026-03-16  
**Status**: Draft  
**Input**: User description: "Two-level analysis. User sends a high-res image and selects an ROI (e.g., right upper). We crop the main image to a square, crop the ROI to a square centered on the ROI, and send both to MedGemma."

## Core Problem

MedGemma's backend (`llama-server`) forces all images into an 896x896 square without preserving the aspect ratio. For typical rectangular medical images (like chest X-rays, which are usually portrait), this causes severe horizontal squashing, altering the appearance of anatomical structures (e.g., making the heart look narrower). Furthermore, squeezing a high-resolution image into 896x896 destroys fine details needed for diagnosing subtle pathologies.

## Solution Concept

To solve both distortion and detail loss, we will introduce a **Two-Image ROI Strategy** for single image uploads:
1.  **Main Image (Undistorted Context)**: We take the original image and crop the center out to make a perfect square, then resize it to 896x896. This prevents the `llama-server` from squashing it, preserving anatomical proportions, though the far edges might be lost.
2.  **ROI Image (High Detail)**: The user selects a specific Region of Interest (ROI) via a button. We mathematically locate that quadrant/region on the original high-resolution image, crop a square window around it, and resize *that* window to 896x896.
3.  Both images are sent to the model simultaneously with an automatic prompt explaining what they are.

## User Scenarios & Testing

### User Story 1 - Single Image ROI Selection (Priority: P1)

As a radiologist, I want to upload a single uncompressed high-resolution image and be prompted to optionally select a specific region (e.g., "Top Right") so that the AI can focus its high-detail analysis on that specific area without distorting the overall anatomy.

**Acceptance Scenarios**:

1. **Given** I am an authorized user, **When** I upload a single uncompressed image as a Document, **Then** the bot replies with a message asking me to select an analysis mode, accompanied by an Inline Keyboard with options like: "🔍 Analyze Full Image", "↗️ Top Right", "↖️ Top Left", "↘️ Bottom Right", "↙️ Bottom Left", "⏺ Center".
2. **Given** I am presented with the ROI selection keyboard, **When** I click "↗️ Top Right", **Then** the bot sends my image to the API with the `top_right` preset. The API processes the image into two square images and returns the analysis.

## Requirements

### Functional Requirements

- **FR-001**: The Telegram bot MUST present an Inline Keyboard for ROI selection *only* when a single uncompressed image is uploaded. It MUST NOT appear for text queries or batch album uploads.
- **FR-002**: The Dispatcher API MUST implement a square-cropping algorithm (Center Crop) for the main image to prevent downstream aspect-ratio distortion.
- **FR-003**: The Dispatcher API MUST implement ROI extraction logic that calculates the center of the chosen quadrant (Top Left, Top Right, Bottom Left, Bottom Right, Center) and crops a square window around it from the original image.
- **FR-004**: If an ROI is selected, the API MUST send exactly two images to the inference worker: the square-cropped Main Image and the square-cropped ROI Image.
- **FR-005**: If an ROI is selected, the API MUST automatically prepend a contextual prompt to the user's text (e.g., "Image 1 is the full overview. Image 2 is a zoomed-in detail of the [ROI Name].").

### Constitution Requirements

- **CR-001**: Feature MUST NOT rely on external web services for image processing; all Pillow manipulation MUST occur in-memory on the Dispatcher server (Principle I & V).

## Success Criteria

- **SC-001**: A portrait rectangular image uploaded with an ROI selection results in the inference worker receiving two perfectly square (1:1 aspect ratio) images, verified by server logs.
- **SC-002**: The anatomical proportions in the processed images are preserved (no stretching/squashing compared to the original).
