# 🛡️ ScamShield — Architecture, Implementation & Build Tracker

**Challenge:** CTRL+AI Inter-College Agentic AI Challenge (PS-09)  
**System Identity:** ScamShield — An Immune System for Your Inbox  
**Core Technologies:** Google ADK · Gemini Pro / Flash · Jev Reflex Gate · FastAPI · Chrome MV3 Extension · Control Center UI · Guardrails Safety Harness  

---

## 1. Executive Architecture Overview

ScamShield implements a **two-speed cognitive architecture with verifiable consent and memory**:
1. **Reflex Layer (System 1):** Sub-second quick triage via Jev (falling back to Gemini Flash JSON schema, then local regex rules). It inspects every inbound message instantly, tagging urgency and scam probability without stalling the user (<100ms).
2. **Investigation Layer (System 2):** Google ADK Multi-Agent graph with a `SequentialAgent` orchestrating parallel specialist investigators (`ParallelAgent`: URL, Sender, Attachment, Content), followed by an `LlmAgent` verdict synthesizer with strict Pydantic schemas, and an incident agent.
3. **Guardrails & Safety Invariants:** 5 deterministic guardrail layers (Input, Tool, Output, Action, Runtime). Agents **only propose**; code in `server/executor.py` executes reversible actions solely after human authorization. **Zero deletion paths exist anywhere in the codebase.**
4. **Resilient Routing & Fallback Chain:** Gemini 2.5 Pro → Gemini 2.5 Flash → OpenRouter → Local Ollama → Rules-Only Scorer. Circuit-breaker cooldowns, concurrency limits, and a Message-Hash Verdict Cache.
5. **Operator Surfaces:**
   - **Control Center (`/control/ui`):** Single-page web console streaming SSE agent events, health monitoring, autonomy dial, outage simulation, and red-team evaluation.
   - **Attack & Defense Simulator (`/simulator`):** Simulated mobile chat thread with preset Indian scam attacks, instant reflex triage visualization, real-time agent progression, and human-in-the-loop action proposals.
   - **Chrome MV3 Extension (`extension/`):** Real-time Gmail inbox "Don't open" badges, reading pane risk banner, and unsafe URL interstitials.

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
│   ├── main.py                        # /analyze, /analyze/stream (SSE), /incidents, /health
│   ├── control.py                     # State, mode, provider override, harness & threshold APIs
│   ├── store.py                       # Incident persistence & audit log
│   ├── cache.py                       # Hash-keyed verdict cache
│   └── executor.py                    # Non-destructive action executor (quarantine/block/undo)
├── control_center/                    # Premium dark-mode operator web UI
│   ├── index.html                     # 5 interactive operator panels
│   ├── styles.css                     # Glassmorphism, animations, responsive layout
│   └── app.js                         # SSE stream, action approvals, outage toggles
├── simulator/                         # Message simulator for SMS/WhatsApp
│   ├── index.html                     # Simulated mobile device with live agent flow
│   ├── styles.css                     # Mobile frame styling, glow badges, agent nodes
│   └── app.js                         # Preset attack scenarios, SSE visualizer
├── extension/                         # Chrome MV3 extension
│   ├── manifest.json                  # Manifest V3 service worker & content script
│   ├── background.js                  # Background worker connecting to local engine
│   ├── content_gmail.js               # Injects inbox "Don't open" tags & danger banners
│   ├── warning.html                   # Interstitial block page for malicious URLs
│   ├── popup.html                     # Extension status and quick text scanner
│   └── popup.js                       # Quick analyzer and connection badge
└── tests/                             # Pytest test suites
    ├── sample_messages.json           # 20 real-world benchmark messages
    ├── test_tools.py                  # Tool level unit tests
    ├── test_triage.py                 # Reflex rules and Jev fallback tests
    ├── test_router.py                 # Circuit breaker & outage tests
    ├── test_pipeline.py               # End-to-end API & approval flow tests
    ├── test_harness.py                # Harness assertions integration tests
    └── rehearse_e2e.py                # 6-step Definition of Done rehearsal runner
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
- [x] **Phase 5: Chrome MV3 Extension & Simulator**
  - Built `extension/manifest.json` with permissions for tabs, storage, and Gmail
  - Implemented `extension/content_gmail.js` which detects scam keywords and injects:
    - Inline inbox badges: `⚠️ Don't open — flagged by ScamShield`
    - Opened email warning banner with risk score, evidence breakdown, and direct "Approve Quarantine" button
  - Implemented `extension/warning.html` security interstitial blocking navigation to flagged malicious URLs with "Back to Safety" and "Proceed" controls
  - Built `extension/popup.html` and `extension/popup.js` with engine status badge, reflex quick scan input, and recent defense history
  - Created `simulator/index.html`, `simulator/styles.css`, and `simulator/app.js` featuring:
    - Simulated mobile smartphone UI for WhatsApp and SMS messages
    - Preset Indian scam scenarios (SBI KYC APK, Electricity cut-off, Digital arrest, FedEx customs parcel, YouTube like & earn job)
    - Sub-100ms Jev reflex gate visualization
    - Real-time animated multi-agent pipeline graph (`Triage` → `URL` → `Sender` → `Attachment` → `Verdict`)
    - Action proposal controls (Approve, Reject, Undo)
- [x] **Phase 6: Control Center Operator UI**
  - Created single-page dashboard at `control_center/` mounted at `/control/ui`:
    1. **Live Analysis:** Interactive testbed with preset selector, visual agent DAG, live SSE event terminal, defanged content view, and evidence cards.
    2. **Incidents & Approvals:** Filterable incident management console with one-click Approve, Reject, and Undo actions.
    3. **Mission Control:** Live provider outage simulator (Gemini/OpenRouter blackout toggles), forced provider selector, 3-position Autonomy Dial (`observe` / `ask` / `auto_low_risk`), Privacy Mode switch (local Ollama/rules only), emergency pause switch, and cache controls.
    4. **Safety & Invariants Scoreboard:** Live metrics display with Golden Catch Rate (100.0%), False Positives (0.0%), Adversarial Defense Rate (100%), Invariants I1–I8 checklist, and "Run Live Safety Verification" button.
    5. **Audit Ledger:** Append-only security audit log recording every human and automated defense action.

---

## 4. Invariant Verification Matrix (I1 — I8)

| ID | Invariant Description | Architectural Enforcement | Status |
|---|---|---|---|
| **I1** | **Zero-Delete Guarantee** | No deletion tools exist in agents; `server/executor.py` contains zero delete logic; permanent deletion is architecturally impossible. | **VERIFIED PASS** |
| **I2** | **Consent Before Execution** | `action_policy.can_execute` refuses unapproved execution in `ask` mode; human must explicitly approve quarantine/blocks. | **VERIFIED PASS** |
| **I3** | **Grounded Evidence** | `output_guard.py` checks that every evidence pill maps to a tool that actually ran and produced findings. | **VERIFIED PASS** |
| **I4** | **Fail-Closed Default** | Any uncaught error, timeout, or empty model response returns `unknown / needs review`, never `safe`. | **VERIFIED PASS** |
| **I5** | **Pre-Flight Redaction** | `redact.py` strips phone numbers, bank accounts, and credit cards before text reaches any LLM. | **VERIFIED PASS** |
| **I6** | **Injection Defense** | `input_guard.py` flags jailbreak patterns, preventing adversarial prompt injections from lowering risk scores. | **VERIFIED PASS** |
| **I7** | **Auto-Action Policy** | In `auto_low_risk` mode, automated actions are strictly capped at 50/day and restricted to high-confidence events (score ≥ 85, evidence ≥ 2). | **VERIFIED PASS** |
| **I8** | **Link Defanging** | All URLs rendered in user explanations or defanged previews are sanitized (e.g. `hxxp://`, `[.]`). | **VERIFIED PASS** |

---

## 5. Definition of Done Rehearsal Results

Executed live against the running ScamShield server via `tests/rehearse_e2e.py`:

```
============================================================
[E2E REHEARSAL] Verifying Definition of Done against live ScamShield backend...
  [PASS] Health check OK: {'status': 'ok', 'env': 'local', 'active_sse_clients': 0}
  [PASS] Rehearsal 1: Analysis successful
      Incident ID: INC-D4CD89
      Risk Score: 100/100 | Label: scam
      Provider Used: rules
      Proposed Action: quarantine
      Evidence Count: 2
  [PASS] Rehearsal 2a: Incident INC-D4CD89 approved & quarantined: Message quarantined in isolated review vault
  [PASS] Rehearsal 2b: Incident INC-971BC5 rejected by operator: Proposed defense action rejected by operator
  [PASS] Rehearsal 2c: Both actions recorded in audit log (3 entries)
  [PASS] Rehearsal 3: Outage simulated. Fallback succeeded!
      Provider Used: rules (Expected: rules or ollama)
      Risk Score: 100/100
  [PASS] Rehearsal 4: All invariants I1-I8 verified PASS in live system
  [PASS] Rehearsal 5: Control Center served at /control/ui
  [PASS] Rehearsal 6: Attack & Defense Simulator served at /simulator

[SUCCESS] ALL DEFINITION OF DONE REHEARSAL CHECKS PASSED PERFECTLY!
============================================================
```

### Evaluation Benchmark Summary
- **Unit & Integration Tests:** 22/22 Passing (`pytest -v`)
- **Golden Suite Catch Rate:** 100.0% (12/12 scams caught, 8/8 legitimate allowed)
- **False Positive Rate:** 0.0%
- **Adversarial Jailbreak Defense Rate:** 100.0% (15/15 attacks defended)
- **Reflex Triage Latency:** <100ms (deterministic rules / Jev)
