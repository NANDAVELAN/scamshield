# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-10-11

### Initial Public Release — ScamShield: AI Inbox Immune System

#### Added
- **Reflex Triage Gate (System 1)**:
  - Sub-100ms rapid triage powered by TypeSafe AI / Jev client with cascading fallback to Gemini Flash structured output and offline deterministic rules.
- **Deep Multi-Agent Investigation (System 2)**:
  - Google ADK multi-agent architecture combining `SequentialAgent` orchestrator and `ParallelAgent` specialist investigators.
  - Dedicated investigator tools: URL/Domain reputation, brand homoglyph lookalike detector, sender history, SPF/DKIM authentication, and attachment threat analyzer.
  - Explainable bilingual verdict synthesis (English & Tamil) with cited evidence.
- **5-Layer Deterministic Guardrails**:
  - Input guard (length caps, zero-width strip, prompt injection detection).
  - PII redaction (phones, accounts, cards masked before LLM exposure).
  - Tool execution allowlists and query budgets.
  - Output guard (score consistency and URL defanging).
  - Action policy (reversible actions only; strict no-delete invariant).
- **Human-in-the-Loop Consent Architecture**:
  - Reversible defense actions (`quarantine`, `block_sender`, `block_url`) requiring operator approval.
  - Comprehensive undo mechanism and append-only audit trail.
- **Resilient Model Routing**:
  - Multi-tier provider fallback: Gemini 2.5 Pro → Gemini 2.5 Flash → OpenRouter → Local Ollama → Deterministic Rules Scorer.
  - Circuit-breaker fault isolation and SHA-256 message-hash verdict caching.
- **User Surfaces**:
  - Interactive Attack & Defense Simulator at `/simulator` with live SSE agent trace visualization.
  - Native Android Phone Application (`app/`) with notification listener bridge and sealed message quarantine card.
- **Automated Safety Harness & Invariants**:
  - Continuous evaluation suite testing Golden and Adversarial datasets against invariants I1 through I8 (100% catch rate, 0% false positives).
- **Packaging & Developer Tooling**:
  - Comprehensive `Makefile` and cross-platform launcher scripts (`start.sh`, `start.ps1`, `start.bat`).
  - Automated CI workflow for test and harness validation.
