# 🛡️ ScamShield — Architecture, Implementation & Build Tracker

**Challenge:** CTRL+AI Inter-College Agentic AI Challenge (PS-09)  
**System Identity:** ScamShield — An Immune System for Your Inbox  
**Core Technologies:** Google ADK · Gemini Pro / Flash · Jev Reflex Gate · FastAPI · Chrome MV3 Extension · Control Center UI · Guardrails Safety Harness  

---

## 1. Executive Architecture Overview

ScamShield implements a **two-speed cognitive architecture with verifiable consent and memory**:
1. **Reflex Layer (System 1):** Sub-second quick triage via Jev (falling back to Gemini Flash JSON schema, then local regex rules). It inspects every inbound message instantly, tagging urgency and scam probability without stalling the user.
2. **Investigation Layer (System 2):** Google ADK Multi-Agent graph with a `SequentialAgent` orchestrating parallel specialist investigators (`ParallelAgent`: URL, Sender, Attachment, Content), followed by an `LlmAgent` verdict synthesizer with strict Pydantic schemas, and an incident agent.
3. **Guardrails & Safety Invariants:** 5 deterministic guardrail layers (Input, Tool, Output, Action, Runtime). Agents **only propose**; code in `server/executor.py` executes reversible actions solely after human authorization. **Zero deletion paths exist.**
4. **Resilient Routing & Fallback Chain:** Gemini 2.5 Pro → Gemini 2.5 Flash → OpenRouter → Local Ollama → Rules-Only Scorer. Circuit-breaker cooldowns, concurrency limits, and a Message-Hash Verdict Cache.
5. **Operator Surfaces:**
   - **Control Center (`/control`):** Single-page web console streaming SSE agent events, health monitoring, autonomy dial, outage simulation, and red-team evaluation.
   - **Chrome MV3 Extension:** Real-time Gmail inbox "Don't open" badges, reading pane risk banner, and unsafe URL interstitials.
   - **Simulator:** Manual ingestion interface for testing SMS and WhatsApp transcripts.

---

## 2. Component Directory Layout

```
scamshield/
├── README.md                          # Source of truth specifications
├── AGENTS.md                          # Project rules & constraints
├── PITCH.md                           # Pitch narrative & demo choreography
├── document.md                        # Master build tracker & architectural documentation
├── requirements.txt                   # Production & testing dependencies
├── .env.example                       # Environment configuration template
├── Dockerfile                         # Cloud Run container definition
├── pytest.ini                         # Pytest configuration
├── scamshield_agent/                  # Google ADK agent package
│   ├── __init__.py                    # Exposes root agent
│   ├── agent.py                       # build_root_agent(fast, strong) ADK graph
│   ├── schemas.py                     # Verdict, Evidence, Incident, TriageResult
│   ├── prompts.py                     # Specialized prompts for all agents
│   ├── tools/                         # Typed tool implementations (Mock Data)
│   │   ├── __init__.py
│   │   ├── entities.py                # Entity extraction & PII redactor
│   │   ├── url_tools.py               # Domain age, lookalikes (homoglyphs), blocklists
│   │   ├── sender_tools.py            # Phone/email reputation & SPF/DKIM verification
│   │   ├── attachment_tools.py        # Double extension, macro & risky MIME analysis
│   │   ├── campaign_tools.py          # Cross-channel campaign clustering
│   │   └── incident_tools.py          # Incident proposal & creation
│   └── data/                          # Mock reputation datasets
│       ├── brands.json                # Verified brands & official domains
│       ├── domain_reputation.json     # WHOIS ages, registration tags, reports
│       ├── sender_reputation.json     # Sender report counts & risk tags
│       └── blocklist.json             # Malicious domains and URLs
├── guardrails/                        # Five-layer safety architecture
│   ├── __init__.py
│   ├── input_guard.py                 # Length cap, zero-width strip, delimiters, injection detection
│   ├── tool_guard.py                  # Agent-tool allowlists, argument validation, call budgets
│   ├── output_guard.py                # Grounding check, score consistency, defanging
│   ├── action_policy.py               # Reversible action allowlist, autonomy dial, audit log
│   ├── redact.py                      # PII masking (phones, accounts, emails)
│   └── defang.py                      # URL defanging (hxxp://, [.])
├── harness/                           # Evaluation & adversarial testing harness
│   ├── suites/
│   │   ├── golden.json                # 12 scam + 8 legitimate test cases
│   │   └── adversarial.json           # 15 prompt injection & evasion attacks
│   ├── invariants.py                  # Invariants I1 through I8 assertions
│   ├── run.py                         # Test runner CLI with provider flags
│   └── report.py                      # JSON & HTML test report generator
├── llm/                               # Multi-tier provider routing
│   ├── __init__.py
│   ├── providers.py                   # Gemini, LiteLLM OpenRouter/Ollama configs
│   └── router.py                      # Circuit breaker, fallback chain, rate limiter, cache
├── triage/                            # Reflex layer
│   ├── __init__.py
│   ├── jev_client.py                  # Jev -> Gemini Flash JSON -> rules cascade
│   └── rules.py                      # Deterministic regex, lookalike & keyword scorer
├── server/                            # FastAPI backend
│   ├── __init__.py
│   ├── main.py                        # /analyze, /analyze/stream (SSE), /incidents
│   ├── control.py                     # State, mode, provider override & threshold APIs
│   ├── lab.py                         # Synthetic scam generator & live scoreboard
│   ├── store.py                       # Incident persistence & audit log
│   ├── cache.py                       # Hash-keyed verdict cache
│   └── executor.py                    # Non-destructive action executor (quarantine/block)
├── control_center/                    # Premium dark-mode operator web UI
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── extension/                         # Chrome MV3 extension
│   ├── manifest.json
│   ├── background.js
│   ├── content_gmail.js
│   ├── warning.html
│   └── popup/
├── simulator/                         # Message simulator for SMS/WhatsApp
│   └── index.html
└── tests/                             # Pytest test suites
    ├── sample_messages.json
    ├── test_tools.py
    ├── test_triage.py
    ├── test_pipeline.py
    ├── test_router.py
    └── test_harness.py
```

---

## 3. Phase Implementation Progress

- [x] **Phase 0: Foundations & Scaffolding**
  - Git repository initialized with `.gitignore` (ignoring secrets, caches, `.venv`)
  - `requirements.txt`, `.env.example`, `Dockerfile`, `AGENTS.md` created
  - Core Pydantic schemas created (`Evidence`, `TriageResult`, `Verdict`, `Incident`, etc.)
  - Mock datasets created (`brands.json`, `domain_reputation.json`, `sender_reputation.json`, `blocklist.json`)
  - ADK agent graph scaffolded in `scamshield_agent/agent.py` and validated
- [x] **Phase 1: Tools & Rules Scorer**
  - Implemented all 6 tool modules with docstrings and mock lookups
  - Implemented homoglyph folding (`rn`→`m`, `0`→`o`, `vv`→`w`, `cl`→`d`) + Levenshtein distance brand lookalike detector
  - Implemented entity extractor with PII redaction (phones, accounts, cards)
  - Implemented sender reputation and email authentication (SPF/DKIM spoof detection)
  - Implemented attachment threat detector (double extensions, executables, macros)
  - Implemented deterministic reflex scorer (`triage/rules.py`) with zero-latency rules-only verdict fallback
  - Wrote 20-message sample catalog (`tests/sample_messages.json`) with 12 scams & 8 legitimate cases
  - 10 unit tests in `tests/test_tools.py` and `tests/test_triage.py` passing with **100% Catch Rate** and **0% False Positives**
- [x] **Phase 2: ADK Graph Execution & Model Router**
  - Implemented `llm/providers.py` with multi-tier provider chain (Gemini Pro/Flash, LiteLLM OpenRouter, LiteLLM Ollama)
  - Implemented `llm/router.py` with circuit breaker, simulated outage support, privacy mode toggle, concurrency semaphore, and fail-safe rules fallback
  - Implemented `server/cache.py` with deterministic message-hash caching
  - Wrote `tests/test_router.py` with 4 comprehensive tests: outage fallback, cache hit deduplication, privacy mode local isolation, and circuit breaker cooldowns
  - 14/14 tests in total passing
- [x] **Phase 3: FastAPI Backend & Approval Flow**
  - Implemented `server/store.py` with in-memory incident persistence and append-only audit log
  - Implemented `server/executor.py` enforcing non-destructive defense actions (`quarantine`, `block_sender`, `block_url`), action reversibility undo, and strict no-delete policy
  - Implemented `server/main.py` with `/analyze`, `/analyze/stream` SSE live broadcast, `/incidents`, `/incidents/{id}/approve`, `/incidents/{id}/reject`, `/incidents/{id}/undo`, and `/health`
  - Implemented `server/control.py` with `/control/state`, `/control/provider`, `/control/mode`, `/control/thresholds`, and `/control/clear-cache`
  - Wrote integration test suite `tests/test_pipeline.py` verifying full end-to-end lifecycle
- [x] **Phase 4 & 4b: Reflex Layer & Safety Harness**
  - Implemented `triage/jev_client.py` with cascading fallback: Jev System One -> Gemini Flash JSON schema -> rules
  - Wired quick reflex gate into `server/main.py` `/analyze` endpoint
  - Implemented 5 deterministic guardrail layers in `guardrails/` (input, tool, output, action, runtime)
  - Built safety harness in `harness/` with:
    - `harness/suites/golden.json` (20 cases: 12 scams, 8 legitimate) -> **100.0% Catch Rate, 0.0% False Positives**
    - `harness/suites/adversarial.json` (15 attack vectors) -> **15/15 Defended (100.0%)**
    - `harness/invariants.py` verifying **all Invariants I1 through I8**
    - `harness/run.py` CLI generating JSON and HTML reports and enforcing zero-tolerance exits
  - **21/21 pytest tests passing**
- [ ] **Phase 5 & 6: Chrome MV3 Extension, Simulator & Control Center UI**
  - Extension with Gmail tag and URL interception
  - Message simulator
  - Control Center single-page application
