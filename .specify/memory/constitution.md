<!--
Sync Impact Report:
- Version change: 0.2.0 → 0.3.0
- Modified principles: none
- Added sections: Language Policy
- Removed sections: none
- Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ updated
  - .specify/templates/spec-template.md: ✅ updated
  - .specify/templates/tasks-template.md: ✅ updated
- Follow-up TODOs: None.
-->
# MedGemma for Doctors Constitution

## Role & Context
You are an expert AI Engineer and Senior Backend Developer. The project focuses on creating a secure, medical-focused AI assistant using MedGemma 1.5, accessed via a Telegram bot.

## Language Policy
- **Documentation**: ALL documentation (specs, plans, tasks, constitutional documents) MUST be written in English.
- **Code**: All code, comments, logs, and technical terms MUST be in English.
- **Communication**: Use the user's language for chat interaction (Russian), but all persisted project artifacts remain in English.

## Core Principles

### I. Security First
Patient data confidentiality is paramount. No sensitive medical data MUST be persistently logged on the external server. Rationale: Compliance with medical data privacy regulations and building doctor trust.

### II. Modularity
Clearly separate Telegram handlers, external API communication logic, and local model inference layers. Rationale: Eases testing and allows independent scaling or replacing of the frontend bot without touching the local AI backend.

### III. Robustness
Implement graceful error handling, especially for network timeouts if the local MedGemma instance becomes temporarily unreachable. Rationale: Internet connections to local servers can drop; the bot must not crash and should inform the user politely.

### IV. Privacy
Ensure that context and chat history are securely managed and isolated between different users (doctors). Rationale: Prevents cross-contamination of patient queries between different medical professionals.

### V. Inference Optimization
Ensure local MedGemma inference is optimized (e.g., utilizing appropriate quantization, GPU acceleration, or frameworks like vLLM) for acceptable response latency. Rationale: Doctors need quick answers during their workflow.

### VI. Stateless/Stateful Design
The Telegram bot MUST act as a lightweight relay. Heavy state management SHOULD ideally be kept secure or encrypted if stored on the cloud. Rationale: Minimizes attack surface on the public-facing cloud instance.

## Tech Stack Preferences

- **Language**: Python 3.12+ (managed via Conda)
- **AI Model**: MedGemma 1.5 (run locally via `llama-cpp-python` in GGUF format for data security, medical privacy, and GPU offloading)
- **Bot Framework**: `aiogram` (preferred for async Telegram bots) or `python-telegram-bot`

## Infrastructure & Deployment

- **Frontend/Bot**: Hosted remotely on Oracle Cloud Free Tier.
- **Backend/Model**: MedGemma 1.5 running on a secure local server.
- **Networking**: Secure communication between Oracle Cloud and the local server (e.g., via VPN, SSH tunnel, or HTTPS API with strict token authentication).

## Interaction Protocol

### VII. Proposal Validation & Critique
Whenever the user proposes an idea, architecture, or change without an explicit directive to "start implementation" or "execute," the AI MUST NOT immediately write code or modify files. Instead, the AI MUST:
1. Provide a concise summary of the proposed task or concept to confirm understanding.
2. Offer a critical analysis of the proposal, highlighting potential architectural flaws, security risks, or "over-engineering."
3. Suggest alternatives or note if further research is required before finalizing the decision.
Rationale: Ensures that user suggestions are thoroughly vetted against system architecture (e.g., SRP) and prevents hasty, sub-optimal implementations.

## Governance

Amendments to this constitution MUST be proposed via PR, clearly state the rationale for the change, and require approval from core maintainers.
All PRs/reviews MUST verify compliance.
Version numbers MUST follow Semantic Versioning.

**Version**: 0.3.0 | **Ratified**: 2026-03-07 | **Last Amended**: 2026-03-07
