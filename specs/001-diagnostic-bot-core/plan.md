# Implementation Plan: Diagnostic Bot Core

**Branch**: `001-diagnostic-bot-core` | **Date**: 2026-03-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-diagnostic-bot-core/spec.md`

## Summary

Build a Telegram bot hosted on Oracle Cloud that acts as a secure, stateless relay. It receives text queries and medical images (X-ray/MRI) from whitelisted doctors, forwards them via a Reverse SSH Tunnel to a local secure server running MedGemma 1.5, and returns the diagnostic reports. User sessions and context are isolated and automatically cleared after 24 hours of inactivity.

## Technical Context

**Language/Version**: Python 3.12+ (managed via Conda)
**Primary Dependencies**: `aiogram` (bot framework), `FastAPI` (local inference API), `httpx` (async HTTP client for bot), `pydantic` (data validation), `google-api-python-client` (for Google Drive whitelist fetch)
**Storage**: SQLite (for managing user sessions, context history, and caching the whitelist on the local server), Google Drive (source of truth for whitelist)
**Testing**: `pytest`, `pytest-asyncio`, `pytest-httpx`
**Target Platform**: Oracle Cloud Free Tier (Bot Frontend) and Local Linux Server with GPU (MedGemma Backend)
**Project Type**: Telegram Bot + Local REST API Backend
**Performance Goals**: End-to-end response <15s for typical text queries; timeouts handled within 30s.
**Constraints**: Zero persistent logging of patient data on Oracle Cloud. All state must be managed locally.
**Scale/Scope**: Small scale (a few whitelisted doctors), high latency tolerance for complex medical inference.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Does it ensure patient data confidentiality? (Principle I: Security First)
- [x] Are Telegram handlers, API logic, and inference separated? (Principle II: Modularity)
- [x] Is graceful error handling implemented for network timeouts? (Principle III: Robustness)
- [x] Is user context isolated? (Principle IV: Privacy)
- [x] Is the Telegram bot acting as a lightweight relay? (Principle VI: Stateless/Stateful Design)

## Project Structure

### Documentation (this feature)

```text
specs/001-diagnostic-bot-core/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── local-inference-api.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
├── bot/                 # Oracle Cloud deployment
│   ├── handlers/        # Telegram message handlers
│   ├── services/        # Logic to forward requests to local API
│   ├── config.py
│   └── main.py          # Entry point for aiogram
├── api/                 # Local Server deployment
│   ├── routes/          # FastAPI endpoints
│   ├── services/        # MedGemma inference integration
│   ├── db/              # SQLite session and whitelist management
│   ├── config.py
│   └── main.py          # Entry point for FastAPI
└── shared/              # Shared models/schemas (if applicable)
    └── schemas.py

tests/
├── bot/
└── api/
```

**Structure Decision**: A dual-module structure (`src/bot` and `src/api`) to clearly separate the Oracle Cloud frontend and the Local Backend, as mandated by the Constitution (Principle II).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
