# Implementation Plan: MedGemma Inference Strategy (GBNF & Cache Management)

**Branch**: `005-medgemma-strategy` | **Date**: 2026-03-14
**Input**: Feature specification from `/specs/005-medgemma-strategy/spec.md`

## Summary

Implement strict inference formatting, GBNF grammar, and optimal KV Cache management strategies for MedGemma. This addresses hardware constraints (avoiding `-c 8192` OOMs via `-c 6144` or `-np 3` slot division) and mitigates hallucination issues inherent to the Gemma architecture on `llama-server`. It includes exploring a custom `.jinja` template to cleanly handle system prompts.

## Technical Context

**Language/Version**: Python 3.12+ (FastAPI dispatcher), C++ (llama-server)
**Primary Dependencies**: `httpx`, `aiosqlite`
**Target Platform**: Linux server connecting to local `llama-server` instances.
**Project Type**: Web-service (Dispatcher API)
**Constraints**: Tight VRAM margins (~6GB total require `-c 6144` to avoid CLIP buffer OOMs), KV cache slot division (`-np 3` for multi-role concurrency or `-np 1` with manual flushing), strict Jinja template formatting requiring either Python injection or a custom `.jinja` file.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Does it ensure patient data confidentiality? (Principle I: Security First)
- [x] Are Telegram handlers, API logic, and inference separated? (Principle II: Modularity)
- [x] Is graceful error handling implemented for network timeouts? (Principle III: Robustness)
- [x] Is user context isolated? (Principle IV: Privacy) - *Yes, enforced by KV cache flushing.*
- [x] Is the Telegram bot acting as a lightweight relay? (Principle VI: Stateless/Stateful Design)

## Project Structure

### Documentation (this feature)

```text
specs/005-medgemma-strategy/
├── plan.md              
├── spec.md        
└── tasks.md             
```

### Source Code

The primary logic will reside in the Dispatcher API:

```text
src/
└── api/
    └── services/
        └── chat_manager.py  # Add GBNF logic and stateful cache invalidation tracking
```

**Structure Decision**: The logic will be added to the existing `ChatManager` service layer to maintain the existing architecture, modifying the `dispatch_inference_to_worker` flow.
