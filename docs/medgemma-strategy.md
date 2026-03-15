# Optimal Strategy for MedGemma Dialog and Inference Configuration

This document outlines the strategy for running MedGemma-1.5-4B via `llama-server` on a GTX 1060 (6GB VRAM), based on a comprehensive review of meta-research (GPT, Grok, Sonnet) and empirical startup logs.

## 1. Context Length Analysis & VRAM Risks (6144 vs 8192)

Based on the startup logs (`llama.cpp.start.6144.txt` and `llama.cpp.start.8192.txt`) running on the GTX 1060 (Total VRAM: 6064 MiB):

*   **Base Model Load:** The model and visual projector consume exactly the same VRAM (~3036 MiB).
*   **The Hidden Danger (Compute Buffers):** The meta-research explicitly warns that when processing images (`--mmproj`), the compute buffers for the CLIP encoder scale drastically with context size. At `-c 8192`, the compute buffers and dynamic allocations balloon significantly (often exceeding 500 MiB under load), leaving alarmingly tight margins.
*   **Conclusion:** While `-c 8192` technically starts, it leaves very little free VRAM (~1.4 GB) and risks Out-of-Memory (OOM) errors during heavy generation or concurrent requests. **Operating at `-c 6144` is strongly recommended** as the optimal safe threshold for the GTX 1060. Alternatively, if `8192` is strictly required, you must use `--gpu-layers N` (instead of `-ngl 24` or `-1`) to offload some LLM layers to system RAM to free up VRAM for the compute buffers.

**Update based on benchmark testing (2 images, GBNF enabled):**
A stress test with two 1024x1024 PNG images at `-c 6144 -np 3` peaked at exactly 4592 MiB VRAM. This leaves ~1.4 GB of safe headroom. 
*   **Future Exploration (8-bit Quantization):** Since the 6-bit (Q6_K) or 4-bit (Q4_K_M) models leave 1.4 GB free, it is mathematically viable to test an 8-bit quantized model (Q8_0) within the same `-c 6144` context limit to see if diagnostic accuracy improves without hitting OOM.
*   **Future Exploration (8192 Context):** With 1.4 GB free, pushing the context back to `8192` (while keeping the current model) is also a highly viable experiment for processing larger batches of images simultaneously.

## 2. KV Caching and Slot Architecture (`-np`)

The research clarifies a critical misunderstanding regarding slots (`-np`):
*   **Slot Division, Not Multiplication:** Using `-np N` (slots) does NOT multiply the total context memory; it **divides the existing `-c` memory**. For example, `-c 6144 -np 3` gives you 3 slots of 2048 tokens each, fitting in the exact same memory footprint as 1 slot of 6144 tokens.
*   **The Multi-Slot Architecture:** Instead of forcing `-np 1` and manually flushing the cache via the API Gateway every time a user changes, we can permanently dedicate slots. For example, `slot 0` for Radiologists, `slot 1` for Patients. The server keeps both system prompts cached simultaneously in VRAM, yielding instant responses for both user types without explicit cache flushing.
*   **Fallback (Single Slot):** If full context (6144) is needed per user, we stick to `-np 1`. In this case, the Dispatcher MUST explicitly send a slot reset command (`{"id_slot": 0, "messages": [], "cache_prompt": false}`) when the user type changes to prevent VRAM fragmentation.

## 3. Dialog Construction & Jinja Formatting

Gemma architectures have strict formatting requirements and reject the native `system` role.

*   **Required Server Flags:** To ensure the C++ server formats tokens correctly, it MUST be started with the exact flags: `--chat-template gemma --jinja` (and `--cache-reuse 1`).
*   **Option A: Python Prompt Injection (Current):** The Dispatcher injects the system prompt directly into the first `user` message.
*   **Option B: Custom Jinja File (Cleaner Architecture):** Instead of Python string concatenation, write a custom `.jinja` file that overrides the Gemma template's rejection of the system role, and pass it via `--chat-template-file /path/to/medgemma.jinja`. This allows the Dispatcher to send standard OpenAI JSON (with `"role": "system"`).
*   **Guardrails & Forced Grammar (GBNF):** For maximum reliability (reducing hallucinations by 2-3x), use **GBNF (GGML BNF) grammar** in `llama-server` to physically restrict the model's output to a strict radiology report structure (`Findings: ... Impression: ...`).

## 4. Multi-Image Workflow ("Before & After")

The system must be capable of receiving a group of images (e.g., an album of two X-rays) to perform comparative analysis (e.g., assessing disease progression from 2023 to 2024).

*   **Telegram Media Groups:** When a user sends an album, Telegram splits it into separate messages with a shared `media_group_id`. 
*   **Aggregation Logic:** The bot's message handler must intercept these messages, aggregate the images using the `media_group_id`, and wait for a brief timeout (e.g., 2-3 seconds) to ensure all images in the group have arrived before dispatching them to the API.
*   **API Payload:** The Dispatcher must format the `messages` array to include multiple `{"type": "image_url", ...}` dictionaries in a single `user` turn.
*   **VRAM Constraints:** Processing multiple images simultaneously multiplies the CLIP compute buffer requirements. Our benchmarks confirm that 2 full-resolution PNG images safely fit within a `-c 6144` context (peaking at ~4592 MiB), making this feature fully viable on a GTX 1060.