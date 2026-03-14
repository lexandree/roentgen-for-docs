# Implementation Tasks: MedGemma Inference Strategy

**Branch**: `005-medgemma-strategy` | **Date**: 2026-03-14
**Input**: Feature specification from `/specs/005-medgemma-strategy/spec.md` and `/specs/005-medgemma-strategy/plan.md`

## 1. Implement KV Cache Invalidation

- **Goal**: Prevent VRAM fragmentation and context bleed by explicitly clearing the `-np 1` slot on `llama-server` when the system prompt context changes.
- **Tasks**:
  - [ ] Add `active_system_prompt` tracking in `ChatManager` or database to detect when a new user's system prompt differs from the last evaluated prompt on a specific route.
  - [ ] Implement an explicit reset payload generation: `{"id_slot": 0, "messages": [], "cache_prompt": false}`.
  - [ ] Modify `dispatch_inference_to_worker` to send this reset request to the C++ worker immediately prior to sending the new user's payload.
  - [ ] Ensure `"cache_prompt": true` is included in all standard `llama-server` chat completion payloads to leverage the cache.

## 2. Implement GBNF Grammar Constraints

- **Goal**: Force the `llama-server` to output strictly formatted medical reports, heavily reducing hallucinations and conversational drift.
- **Tasks**:
  - [ ] Define the GBNF string for a standard radiology report (e.g., enforcing `<think>...\n</think>\nFindings:\n...\nImpression:\n...`).
  - [ ] Update the `payload` dictionary in `dispatch_inference_to_worker` (specifically for the `/v1/chat/completions` branch) to include the `grammar` key containing the GBNF definition.
  - [ ] (Optional) Make the grammar definition dynamic based on the user's `system_prompt_type` if different specialties require different GBNF structures.

## 3. Testing and Validation

- **Goal**: Ensure the new cache invalidation doesn't break concurrent usage or degrade performance, and that GBNF grammar allows for valid token generation without failing.
- **Tasks**:
  - [ ] Test KV Cache invalidation by switching between two users with different system prompts and verifying the `llama-server` logs (`slot 0 reset`).
  - [ ] Test GBNF enforcement by sending conversational text and verifying that the response is strictly structured.