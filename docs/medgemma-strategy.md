# MedGemma Dialog and Inference Strategy

This document outlines the core strategy for running MedGemma-1.5-4B efficiently via `llama.cpp` (`llama-server`) within the Roentgen for Docs architecture.

## 1. Context Length, Quantization & VRAM Constraints

Operating multi-modal models like MedGemma requires careful management of context lengths and quantization levels to avoid Out-of-Memory (OOM) errors, especially on hardware with limited VRAM (e.g., 6GB or 8GB GPUs).

*   **Model vs. Compute Allocation:** The base LLM and its visual projector consume a fixed amount of VRAM. However, when processing images (`--mmproj`), the compute buffers for the CLIP encoder scale drastically with the defined context size (`-c`).
*   **Optimal Configuration (8-bit + 8K Context):** By utilizing an 8-bit quantized model (Q8_0) and an 8K context window (`-c 8192`), the system achieves an excellent balance of diagnostic accuracy and memory safety. On a 6GB GTX 1060, VRAM consumption remains incredibly stable (under 5300 MiB), even when analyzing two high-resolution images simultaneously.
*   **Context Extension (Beyond 8192):** Attempting to run at contexts larger than 8192 on 6GB hardware will likely lead to OOM crashes due to ballooning compute buffers. If a larger context is strictly required, you must offload a portion of the LLM layers to system RAM (`--gpu-layers N`).

### Future Explorations
*   **Batch Image Contexts:** If running on larger GPUs (e.g., 12GB+), extending the context significantly beyond `8192` is recommended to support analyzing larger batches of images simultaneously.

## 2. KV Caching and Multi-Slot Architecture

Efficient switching between different user contexts (e.g., a Radiologist profile vs. a Patient profile) relies on `llama.cpp`'s slot architecture.

*   **Slot Division (`-np`):** The `-np N` parameter divides the total allocated context memory (`-c`) into `N` independent slots. For example, `-c 8192 -np 4` creates 4 slots of 2048 tokens each, occupying the same memory footprint as a single 8192-token slot.
*   **Dedicated Prompt Caching:** By utilizing multiple slots, the server can permanently cache different system prompts simultaneously. For instance, `slot 0` can cache the "Radiologist" persona, while `slot 1` caches the "Pediatrician" persona. This yields near-instantaneous first-token responses when switching between users.
*   **Fallback (Single Slot):** If full context length is required for extensive dialog histories, the server should be run with `-np 1`. In this mode, the Dispatcher API must explicitly manage the cache and issue slot reset commands when switching user types to prevent VRAM fragmentation.

## 3. Dialog Construction & Jinja Formatting

Gemma-based models have strict chat formatting requirements and typically reject the standard API `system` role.

*   **Server Configuration:** The C++ server MUST be started with the exact template flags to ensure correct tokenization: `--chat-template gemma --jinja` (along with `--cache-reuse 1`).
*   **Prompt Injection:** The Dispatcher must seamlessly handle the `system` role by injecting its content into the first `user` message before forwarding it to the inference worker. Alternatively, a custom `.jinja` template file can be provided to `llama-server` (`--chat-template-file`) to override the strict validation and natively process `"role": "system"` JSON payloads.
*   **Forced Grammar (GBNF):** To maximize reliability and reduce hallucinations in clinical outputs, inference should be constrained using GBNF (GGML BNF) grammar. This physically restricts the model's token generation to a predefined structure (e.g., forcing a `Findings:` and `Impression:` layout).

## 4. Multi-Image Workflow ("Before & After")

The architecture must support comparative analysis across multiple images (e.g., assessing disease progression).

*   **Aggregation:** When users send multiple images (an Album) via Telegram, they arrive as separate messages with a shared `media_group_id`. The Bot implements a brief debounce window (e.g., 3 seconds) to aggregate these images before dispatching them as a single context.
*   **Payload Structuring:** The Dispatcher API formats the request to the Inference Worker by injecting multiple `{"type": "image_url", ...}` elements into a single `user` turn.
*   **VRAM Impact:** Processing multiple images simultaneously multiplies the CLIP compute requirements. Benchmarks confirm that 2 full-resolution images can be safely processed within a `-c 8192` context on a 6GB GPU using Q8_0 quantization without exceeding 5300 MiB VRAM.