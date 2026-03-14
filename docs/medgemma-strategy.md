# Optimal Strategy for MedGemma Dialog and Inference Configuration

This document outlines the strategy for running MedGemma-1.5-4B via `llama-server` on a GTX 1060 (6GB VRAM), based on a comprehensive review of meta-research (GPT, Grok, Sonnet) and empirical startup logs.

## 1. Context Length Analysis & VRAM Risks (6144 vs 8192)

Based on the startup logs (`llama.cpp.start.6144.txt` and `llama.cpp.start.8192.txt`) running on the GTX 1060 (Total VRAM: 6064 MiB):

*   **Base Model Load:** The model and visual projector consume exactly the same VRAM (~3036 MiB).
*   **The Hidden Danger (Compute Buffers):** The meta-research explicitly warns that when processing images (`--mmproj`), the compute buffers for the CLIP encoder scale drastically with context size. At `-c 8192`, the compute buffers and dynamic allocations balloon significantly (often exceeding 500 MiB under load), leaving alarmingly tight margins.
*   **Conclusion:** While `-c 8192` technically starts, it leaves very little free VRAM (~1.4 GB) and risks Out-of-Memory (OOM) errors during heavy generation or concurrent requests. **Operating at `-c 6144` is strongly recommended** as the optimal safe threshold for the GTX 1060. Alternatively, if `8192` is strictly required, you must use `--gpu-layers N` (instead of `-ngl 24` or `-1`) to offload some LLM layers to system RAM to free up VRAM for the compute buffers.

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