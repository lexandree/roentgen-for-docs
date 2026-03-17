# Roentgen for Docs - MedGemma Diagnostic Bot

## Overview
Roentgen for Docs is a secure, privacy-first diagnostic assistant tailored for medical professionals. It bridges the gap between state-of-the-art open-weights medical LLMs (like MedGemma) and accessible mobile interfaces (Telegram), while strictly maintaining data residency and security.

## Key Features
- **Privacy-First Architecture:** The system separates the public-facing Telegram bot (cloud) from the inference engine (backend). Communication occurs strictly through a secure reverse SSH tunnel, ensuring no patient data is persistently stored on public cloud servers.
- **Advanced Image Preprocessing:** To combat the common issue of LLMs distorting non-square images, the system implements intelligent center-cropping. Furthermore, it offers interactive Region of Interest (ROI) commands, allowing doctors to seamlessly zoom into specific quadrants of an X-ray (e.g., Top Left, Bottom Right) for high-resolution targeted analysis without resolution loss.
- **Optimized Edge Inference:** Designed to run efficiently on consumer hardware (e.g., GTX 1060 6GB) utilizing `llama.cpp` (`llama-server`). It employs a multi-slot KV cache architecture for instantaneous persona switching (e.g., from Radiologist to Pediatrician) and uses GBNF grammar constraints to physically prevent hallucinations and enforce strict clinical reporting formats (`Findings: ... Impression: ...`).
- **Robust Access Control:** Security is enforced via a dual-layer whitelist (a local SQLite database synced with a master Google Drive JSON configuration file), ensuring only authorized personnel can interact with the model.

## Technical Stack
- **Backend / Dispatcher:** Python 3.12+, FastAPI, SQLite.
- **Frontend / Bot Framework:** aiogram (Telegram API).
- **Inference Engine:** `llama.cpp` (C++) running MedGemma-1.5-4B (GGUF).
- **Integrations:** Google Drive API (for remote whitelist and configuration management).
