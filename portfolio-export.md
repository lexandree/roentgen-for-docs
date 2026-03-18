---
title: "Roentgen for Docs"
description: "A secure, privacy-first diagnostic assistant bridging open-weights medical LLMs (MedGemma) with a convenient Telegram interface via a flexible Hybrid/BYOC architecture."
pubDate: 2026-03-18
tags: ["FastAPI", "llama.cpp", "aiogram", "MedGemma", "Edge AI"]
githubUrl: "https://github.com/lexandree/roentgen-for-docs"
featured: false
order: 10
---

## Problem Statement
Medical professionals need access to state-of-the-art diagnostic LLMs (like MedGemma) using ubiquitous, asynchronous communication channels (like Telegram Desktop) for long inference cycles, without compromising patient data privacy or relying on non-compliant, third-party cloud APIs. Existing solutions often store sensitive data persistently, lack convenient conversational interfaces, or fail to handle high-resolution medical imaging without destructive spatial distortion.

## Approach / Architecture
The architecture strictly decouples the public-facing interface from the inference engine to guarantee data residency and security.
- **Hybrid / BYOC Architecture**: A permanent cloud-hosted control plane (Telegram bot + FastAPI dispatcher) securely routes traffic to ephemeral, user-owned inference workers (e.g., a local Clinic PC via Reverse SSH Tunnel, or an on-demand RunPod GPU). Zero persistent patient data resides on the public cloud.
- **Optimized Edge Inference**: Powered by `llama.cpp` (`llama-server`) running an 8-bit quantized MedGemma-1.5-4B model (Q8_0) on consumer hardware (e.g., GTX 1060 6GB). Employs a multi-slot KV cache architecture (`-np 3`) to permanently cache multiple system prompts (e.g., Radiologist vs. Pediatrician personas), enabling near-instantaneous context switching.
- **Advanced Image Preprocessing**: Implements intelligent center-cropping to prevent non-square image distortion by the LLM's visual projector. Features interactive Region of Interest (ROI) commands, allowing doctors to dynamically extract, square-crop, and up-res specific quadrants (e.g., Top Left, Center) for targeted, high-resolution analysis without spatial loss.
- **Strict Output Constraints**: Uses GBNF (GGML BNF) grammar constraints to physically force the model's token generation into structured clinical reporting formats (`Findings: ... Impression: ...`), drastically reducing hallucinations.
- **Robust Access Control**: Dual-layer whitelist system utilizing a local SQLite DB synced with a master Google Drive JSON configuration file for remote role management.

## Results / Metrics
- **Stable 8K Edge Inference**: Successfully deployed a complex multi-modal LLM pipeline on highly constrained consumer hardware (6GB VRAM). By utilizing an 8-bit quantized model (Q8_0) with an 8K context window (`-c 8192`), VRAM consumption remains incredibly stable (under 5300 MiB), even when performing complex comparative analyses across two simultaneous high-resolution images.
- **3x Hallucination Reduction**: Reduced conversational drift and formatting hallucinations by up to 3x via strict GBNF grammar enforcement.
- **Sub-Second Persona Switching**: Achieved instantaneous context switching through the multi-slot KV cache architecture, bypassing the need to constantly flush and recompute the system prompt.
- **100% Data Residency**: Guaranteed complete privacy by ensuring all physical image files and session contexts are purged immediately after inference or upon session expiration.
