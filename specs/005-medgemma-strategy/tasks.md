# Implementation Tasks: MedGemma Inference Strategy

**Branch**: `005-medgemma-strategy` | **Date**: 2026-03-14
**Input**: Feature specification from `/specs/005-medgemma-strategy/spec.md` and `/specs/005-medgemma-strategy/plan.md`

## 1. Optimize KV Cache and Slot Architecture

- **Goal**: Prevent VRAM fragmentation and context bleed while optimizing for different user types without hitting the 6GB VRAM limit.
- **Tasks**:
  - [ ] Evaluate `-np 3` slot division with a reduced context (`-c 6144`). Configure the Dispatcher to route specific user profiles (e.g., Radiologist, Patient) to dedicated `id_slot`s.
  - [ ] **Fallback**: If `-np 1` must be used for maximum context, implement an explicit reset payload generation (`{"id_slot": 0, "messages": [], "cache_prompt": false}`) in the Dispatcher when the active user profile changes.
  - [ ] Ensure `"cache_prompt": true` is included in all standard `llama-server` chat completion payloads to leverage prefix caching.

## 2. Dialog Formatting and Custom Jinja Template

- **Goal**: Cleanly pass system prompts to Gemma without hacky Python string concatenation, preventing template validation errors.
- **Tasks**:
  - [ ] Create a custom `medgemma.jinja` template file in the repository that natively accepts the `system` role.
  - [ ] Document the required launch flags for `llama-server` (e.g., `--chat-template-file medgemma.jinja --jinja`).
  - [ ] Revert the Python Dispatcher's prompt-squashing hack and rely on standard OpenAI API formatting (`{"role": "system"}`).

## 3. Implement GBNF Grammar Constraints

- **Goal**: Force the `llama-server` to output strictly formatted medical reports, heavily reducing hallucinations and conversational drift.
- **Tasks**:
  - [ ] Define the GBNF string for a standard radiology report (e.g., enforcing `<think>...\n</think>\nFindings:\n...\nImpression:\n...`).
  - [ ] Update the `payload` dictionary in `dispatch_inference_to_worker` to include the `grammar` key containing the GBNF definition.

## 4. Testing and Validation

- **Goal**: Ensure the new architecture avoids OOM errors and guarantees structured outputs.
- **Tasks**:
  - [ ] Monitor compute buffer sizes in `llama-server` startup logs to ensure `-c 6144` or `-c 8192` + `--gpu-layers` keeps VRAM safe.
  - [ ] Test GBNF enforcement by sending conversational text and verifying that the response is strictly structured.