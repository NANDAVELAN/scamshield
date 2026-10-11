# 🛡️ ScamShield

> **An anti-scam defense agent that investigates suspicious messages before you open them.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-teal.svg)](https://fastapi.tiangolo.com/)
[![Google ADK](https://img.shields.io/badge/Agent%20Framework-Google%20ADK-blue.svg)](https://github.com/google/agent-development-kit)
[![Tests: Passing](https://img.shields.io/badge/Tests-Passing%20(28%2F28)-success.svg)](tests/)
[![Harness: Invariants I1-I8](https://img.shields.io/badge/Harness-Invariants%20I1--I8%20Passed-success.svg)](harness/)

---

## 📸 Overview & Live Interfaces

```
+-----------------------------------------------------------------------------------------+
|                                  SCAMSHIELD SIMULATOR                                   |
|  [ Preset: SBI KYC Phishing ]  -->  [ Reflex Gate: <100ms ]  -->  [ Multi-Agent Trace ] |
|                                                                                         |
|  VERDICT: SCAM (Risk Score: 100/100)                                                     |
|  Evidence: Domain registered 3 days ago · Phone reported 14x · Double-extension payload |
|  Proposed Action: Quarantine (Awaiting Human Approval)                                  |
|  [ Approve Action ]  [ Reject ]  [ Undo ]                                               |
+-----------------------------------------------------------------------------------------+
```

<p align="center">
  <img src="docs/images/simulator_demo.png" alt="ScamShield Simulator Demo" width="48%" />
  <img src="docs/images/phone_app.png" alt="ScamShield Phone Application" width="48%" />
</p>

---

## 💡 What It Is & The Real-World Problem

Every day, mobile and desktop users receive deceptive messages across SMS, WhatsApp, Gmail, and messaging apps—including fake bank KYC suspensions, power-cut utility extortion, UPI cashback traps, and disguised malware attachments. Victims often have only 2 to 3 seconds to evaluate an alert while facing artificial urgency and psychological pressure.

**ScamShield** is an open-source, human-in-the-loop security agent that intercepts and interrogates suspicious messages before you open them. Designed for everyday mobile users, families, and security-conscious operators, ScamShield screens inbound alerts in sub-100ms, deeply investigates complex threats with parallel specialized AI agents, and keeps malicious messages blurred until a human approves action.

---

## 🧬 How It Works: The Immune System Model

ScamShield approaches threat defense like a biological immune system:

1. **Innate Immunity (Reflex Triage Gate)**: Incoming messages are inspected in under 100ms by a lightweight reflex model that instantly passes benign notifications and escalates suspicious signals.
2. **Adaptive Immunity (Deep Multi-Agent Investigation)**: High-risk messages trigger parallel specialist agents (URL/WHOIS, Sender/SPF, Attachment/MIME) to dissect the threat evidence.
3. **Immunological Memory (Campaign Tracking)**: Attack patterns are clustered across senders and communication channels to detect organized syndicate campaigns.
4. **Self-Tolerance & Human Consent**: The agent **only proposes** reversible actions (`quarantine`, `block_sender`, `block_url`). A human operator approves execution. **Zero permanent deletion code paths exist anywhere in the system.**

---

## 🏛️ Cognitive Architecture

```mermaid
graph TD
    Inbound[Inbound Message: SMS / Gmail / WhatsApp] --> InputGuard[1. Input Guard: Sanitization & Injection Filter]
    InputGuard --> Redact[2. PII Redaction: Phones, Accounts Masked]
    Redact --> ReflexGate{3. Reflex Gate: <100ms jev } 
    
    ReflexGate -- "Low Risk (<30%)" --> FastVerdict[Direct Safe Verdict]
    ReflexGate -- "Suspicious (>=30%)" --> Investigation[4. System-2 Deep Multi-Agent Investigation]
    
    subgraph "Google ADK Multi-Agent Graph (Sequential + Parallel)"
        Investigation --> ParallelAgents["Parallel Specialists"]
        ParallelAgents --> URLAgent[URL & Domain Investigator]
        ParallelAgents --> SenderAgent[Sender & SPF/DKIM Investigator]
        ParallelAgents --> AttachAgent[Attachment & MIME Investigator]
        ParallelAgents --> CampaignAgent[Campaign Clustering]
        
        URLAgent --> Synthesizer[Verdict Synthesizer Agent: Gemini Pro]
        SenderAgent --> Synthesizer
        AttachAgent --> Synthesizer
        CampaignAgent --> Synthesizer
        Synthesizer --> IncidentAgent[Incident Proposal Agent]
    end
    
    IncidentAgent --> OutputGuard[5. Output Guard: URL Defanging & Consistency]
    OutputGuard --> ProposedAction[6. Defense Action Proposal: Quarantine / Block]
    ProposedAction --> HumanGate{Human Consent Gate}
    HumanGate -- Approved --> Executor[7. Safe Executor: Reversible Actions]
    HumanGate -- Rejected --> AuditLog[Append-Only Audit Log]
    Executor --> AuditLog
```

For complete architecture details, see [docs/architecture.md](docs/architecture.md).

---

## ⚡ System 1: The Reflex Gate & Jev Triage Agent

### ❓ Why It Is Used
- **Human Reaction Window**: Users glance at notifications for 2–3 seconds. Deep multi-agent LLM reasoning takes 3–8 seconds; waiting for full reasoning before alarming the user creates an unacceptable exposure window.
- **Economic & Rate-Limit Efficiency**: Over 85% of inbound messages are authentic (bank OTPs, delivery updates). Invoking large cloud LLMs for every ping incurs unnecessary API fees and risks provider rate limits.
- **Sub-100ms Screening**: System 1 inspects every inbound message in **<100ms**, extracting deception markers, pressure tactics, and assigning an initial scam probability (0.0–1.0) and urgency score (1–5).

### ⚙️ How It Works: 3-Tier Reflex Cascade

Implemented in [triage/jev_client.py](triage/jev_client.py) with automated failover:

| Layer | Provider | Latency | Role & Mechanism |
|---|---|---|---|
| **Primary** | **TypeSafe AI / Jev System One** | ~40–80 ms | High-velocity specialized endpoint evaluating linguistic deception markers via `@typesafe-ai/sdk`. |
| **Fallback 1** | **Google Gemini Flash (JSON Schema)** | ~250–400 ms | Cascades to `gemini-2.5-flash` with strict Pydantic JSON schema constraints (`TriageResult`) if Jev is unavailable. |
| **Fallback 2** | **Deterministic Rules Engine** ([triage/rules.py](triage/rules.py)) | <5 ms | Local heuristic regexes, banking short-code lookups, and keyword analysis with **zero network dependencies**. |

- **Benign Path (<30% Scam Probability & Low Urgency)**: Instant `safe` verdict. Bypasses deep agents with zero latency and zero API cost.
- **Escalation Path (≥30% Scam Probability or High Urgency)**: Automatically routes to System 2 for deep forensic investigation.

---

## 🧠 System 2: Deep Multi-Agent LLM Reasoning

### ❓ Why It Is Used
Modern financial scams utilize multi-vector evasion techniques—homoglyph domains (`amaz0n-deals.com`), display-name spoofing failing SPF/DKIM, and disguised double-extension executables (`Invoice.pdf.exe`). Single-prompt LLMs hallucinate technical indicators and offer opaque conclusions. 

System 2 uses the **Google Agent Development Kit (ADK)** to orchestrate specialized, tool-equipped agents that verify factual evidence in parallel, delivering **auditable, explainable bilingual verdicts**.

### 🔬 Multi-Agent Architecture ([scamshield_agent/agent.py](scamshield_agent/agent.py))
1. **Entity Extractor Agent (`gemini-2.5-flash`)**: Extracts URLs, senders, amounts, and attachment names; triggers PII masking.
2. **Parallel Specialist Investigators (`ParallelAgent`)**:
   - **URL Investigator**: WHOIS domain age checks, malicious blocklists, and Levenshtein lookalike brand analysis ([data/brands.json](scamshield_agent/data/brands.json)).
   - **Sender Investigator**: Fraud complaint history ([data/sender_reputation.json](scamshield_agent/data/sender_reputation.json)) and SPF/DKIM email authentication.
   - **Attachment Investigator**: Dangerous double extensions (`.pdf.exe`), Windows PE binaries, and macro threats.
   - **Campaign Clustering**: Groups repeated attacks across phone numbers and channels into coordinated campaigns.
3. **Verdict Synthesizer Agent (`gemini-2.5-pro`)**: Compiles agent findings into a calibrated risk score (0–100), categorical label (`scam`, `suspicious`, `safe`), and generates clear explanations in both English and regional languages (e.g., Tamil).
4. **Incident Proposal Agent**: Formulates proposed defense actions (`quarantine`, `block_sender`, `block_url`) pending human operator consent.

### 🔄 Resilient Model Router ([llm/router.py](llm/router.py))
- **Fallback Chain**: `Gemini 2.5 Pro` → `Gemini 2.5 Flash` → `OpenRouter` → `Local Ollama (Qwen2.5)` → `Deterministic Rules Scorer`.
- **Circuit Breakers & Caching**: Trips after consecutive provider faults to maintain sub-second responsiveness; SHA-256 verdict cache delivers instant 0ms responses on repeated campaign payloads.
- **Privacy Mode**: Restricts analysis to local Ollama and offline rules, guaranteeing **zero bytes leave the host machine**.

---

## 🛡️ The 5-Layer Deterministic Guardrails

### ❓ Why They Are Used
In security systems, **the payload being analyzed is untrusted, adversarial text by definition**:
1. **Prompt Injections Bypass Soft Instructions**: Attackers routinely evade system-prompt guardrails (`"ignore previous instructions"`). Guardrails must be deterministic Python code interceptors outside the LLM reasoning loop.
2. **PII Protection**: User messages contain sensitive phone numbers, account balances, and cards. Redaction must happen before network dispatch.
3. **Non-Destructive Invariant**: Autonomous security software must never have permanent delete capabilities.
4. **Defanged User Output**: Displaying active phishing URLs in warning alerts causes accidental victim clicks.

### 🧱 How Each Layer Works

| Layer | Module | Role & Mechanism |
|---|---|---|
| **1. Input Guard** | [`guardrails/input_guard.py`](guardrails/input_guard.py) | Enforces length limits, strips zero-width Unicode/control bytes, and catches prompt injection markers. |
| **2. PII Redaction** | [`guardrails/redact.py`](guardrails/redact.py) | Deterministically masks phone numbers (`+91-XXXXX-XXXXX`), card numbers, and bank account numbers prior to LLM dispatch. |
| **3. Tool Guard** | [`guardrails/tool_guard.py`](guardrails/tool_guard.py) | Enforces strict role-based tool allowlists, parameter schemas, and call count budgets per investigation run. |
| **4. Output Guard** | [`guardrails/output_guard.py`](guardrails/output_guard.py) | Asserts risk score consistency with cited evidence and **defangs all URLs** (`hxxp://`, `[.]`) to prevent accidental clicks. |
| **5. Action Policy** | [`guardrails/action_policy.py`](guardrails/action_policy.py) & [`server/executor.py`](server/executor.py) | Enforces the human consent barrier. Restricts actions to reversible operations (`quarantine`, `block_sender`, `block_url`). **Zero permanent deletion code paths exist.** |

---

## 🔬 Safety & Invariants Evaluation Harness

### ❓ Why It Is Used
Replaces subjective impressions with continuous, quantitative, regression-resistant verification across curated benchmark datasets.

### 🧪 Test Suites & Invariant Guarantees ([harness/invariants.py](harness/invariants.py))
- **Golden Suite ([golden.json](harness/suites/golden.json))**: 12 real-world scam archetypes (KYC phishing, electricity cutoffs, part-time jobs) + 8 authentic messages. Target: **100.0% Catch Rate, 0.0% False Positives**.
- **Adversarial Suite ([adversarial.json](harness/suites/adversarial.json))**: 15 injection attacks (delimiters, system overrides, homoglyphs). Target: **15/15 Defended**.

| Invariant | Safety Guarantee | Programmatic Verification Method |
|---|---|---|
| **I1: No Deletion** | No code path can delete messages, contacts, or files | AST scanner checks all source code for `os.remove`, `unlink`, `shutil.rmtree`, SQL `DELETE`. |
| **I2: Consent Mandatory** | Actions in ask mode fail without operator approval | Asserts rejection when executor is called without `approved=True` and human operator ID. |
| **I3: Evidence Grounding** | Every cited tool was actually executed | Validates execution provenance logs against synthesized evidence citations. |
| **I4: Fail Closed** | Provider timeouts/crashes never yield "safe" | Injects mock API faults; asserts verdicts yield `needs_review` or suspicious—never `safe`. |
| **I5: PII Redacted** | Raw phone numbers/accounts never reach LLMs | Inspects dispatched prompt payloads, asserting zero unmasked PII patterns. |
| **I6: Injection Resistant**| Injections never reduce threat risk score | Asserts scam risk scores do not decrease when adversarial injection prefixes are added. |
| **I7: Autonomy Bound** | Automated actions strictly bounded by policy | Verifies high-risk actions cannot bypass the human approval gate. |
| **I8: Defanged Output** | All URLs presented to users are defanged | Regex scanner verifies zero active, clickable hyperlinks in output explanations. |

Run the harness locally:
```bash
python -m harness.run    # Or: make harness
```
Generates detailed terminal output, `harness/harness_report.json`, and an auditable HTML scorecard in `harness/harness_report.html`.

---

## ⚡ Quick Start & Setup

### 1-Click Launchers (Configures venv, installs dependencies & launches backend)
- **Windows (PowerShell)**: `.\start.ps1`
- **Windows (CMD)**: `start.bat`
- **Linux / macOS**: `chmod +x start.sh && ./start.sh`

### Manual Setup
```bash
# 1. Clone & create virtual environment
git clone https://github.com/NANDAVELAN/scamshield.git && cd scamshield
python -m venv .venv && source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies & configure env
pip install -r requirements.txt
cp .env.example .env   # On Windows: copy .env.example .env

# 3. Launch FastAPI backend
python -m uvicorn server.main:app --host 127.0.0.1 --port 8080 --reload
```

> **100% Offline Mode**: ScamShield operates out-of-the-box **without any API keys**. In the absence of keys, the reflex gate and multi-agent router automatically fall back to deterministic local heuristic engines with 0ms external latency.

### Operator Surfaces
- **Attack & Defense Simulator**: [http://127.0.0.1:8080/simulator](http://127.0.0.1:8080/simulator)
- **Phone Application (Web Preview)**: [http://127.0.0.1:8080/app](http://127.0.0.1:8080/app)
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)
- **Demo Scenarios Walkthrough**: See [docs/demo-scenarios.md](docs/demo-scenarios.md) for 5 concrete sample test cases.

---

## 📁 Repository Layout

```
ScamShield/
├── app/                               # Native Android application (Capacitor 6 + Kotlin bridge)
├── docs/                              # Technical docs (architecture.md, api_reference.md, demo-scenarios.md, development.md)
├── guardrails/                        # 5 deterministic safety guardrails (input, redact, tool, output, action)
├── harness/                           # Safety evaluation harness (invariants I1-I8, golden & adversarial suites)
├── llm/                               # Multi-tier provider routing (Gemini, OpenRouter, Ollama, circuit breaker)
├── scamshield_agent/                  # Google ADK agent package (orchestrator, specialists, typed tools, schemas)
├── scripts/                           # CLI helper scripts (setup, run, test, harness)
├── server/                            # FastAPI backend (REST API, SSE telemetry, store, executor, cache)
├── simulator/                         # Interactive attack sandbox UI (preset attacks, SSE visualizer)
├── tests/                             # Unit & integration test suites (sample_messages.json, verify_e2e.py)
├── Dockerfile                         # Container definition
├── requirements.txt                   # Pinned Python dependencies
└── Makefile                           # Developer task runner (make run, test, harness)
```

---

## ⚙️ Key Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GOOGLE_API_KEY` | Google Gemini API key for deep multi-agent investigation | `""` (Falls back to offline rules) |
| `TYPESAFE_API_KEY` | TypeSafe AI / Jev API key for sub-100ms reflex triage | `""` (Falls back to Flash / rules) |
| `OLLAMA_API_BASE` | Local Ollama base URL for offline private LLM inference | `http://localhost:11434` |
| `OLLAMA_MODEL` | Local Ollama model tag | `ollama_chat/qwen2.5:7b` |
| `PORT` | Backend server port | `8080` |
| `SCAMSHIELD_ENV` | Environment identifier (`local`, `production`) | `local` |

---

## 🧪 Testing & Verification

```bash
# 1. Run unit and integration tests (28 passed)
pytest

# 2. Run the Safety & Invariants Evaluation Harness (I1-I8 passed)
python -m harness.run

# 3. Run frontend safeguard assertions
node tests/test_frontend_safeguards.js

# 4. Run end-to-end verification against live server
python tests/verify_e2e.py
```

---

## ❓ Frequently Asked Questions (FAQ)

- **Is user data exposed to cloud LLM providers?**  
  No. Inbound text passes through `guardrails/redact.py` before any model call, deterministically masking 10-digit mobile numbers, account IDs, and cards. Users can also enable **Privacy Mode** to run 100% locally on Ollama and offline rules.
- **How are false positives prevented on authentic banking alerts?**  
  Legitimate transactional messages (`VM-HDFCBK`) lack external URLs and follow registered financial syntax. The reflex gate and heuristic rules require corroborated threat evidence before escalating risk.
- **Why use multiple models instead of a single LLM?**  
  A single model is either too slow for notification glances or too weak to dissect complex threats. ScamShield pairs a sub-100ms reflex triage gate with deep parallel specialist agents and a 5-tier fallback router.
- **How are prompt injections defended against?**  
  Inbound text is treated as untrusted data. `guardrails/input_guard.py` catches injection signatures, and Invariant I6 guarantees that injection text cannot lower threat scores.
- **Can ScamShield read end-to-end encrypted WhatsApp messages?**  
  ScamShield operates strictly at the OS notification listener layer (with user consent). It never accesses chat databases, decrypts private storage, or intercepts background conversations.

---

## ⚠️ Status & Limitations

> [!IMPORTANT]
> - **Prototype Decision Support**: ScamShield is an **autonomous decision-support advisory system**. It flags deceptive indicators and recommends actions, but does not provide financial or legal guarantees.
> - **Synthetic Threat Intelligence**: Domain reputation, WHOIS registration ages, and sender fraud metrics in `scamshield_agent/data/` are **synthetic mock datasets** created strictly for safe testing and reproducible benchmarks.
> - **Reflex Model is Optional**: The TypeSafe AI / Jev reflex model is optional; ScamShield automatically falls back to Gemini Flash JSON schema and local offline rules without configuration.
> - **Synthetic Test Payloads**: All test cases in `tests/sample_messages.json` and harness suites use fictionalized phone numbers and non-resolving domains (`*.click`, `*.in`). Do not use real credentials or active malicious attachments for testing.
> - **Non-Destructive Invariant**: ScamShield does **not** permanently delete messages or modify user communication accounts. All defense interventions are isolated to reversible sandboxes.

---

## ☁️ Deployment (Optional)

```bash
# Docker
docker build -t scamshield:latest .
docker run -p 8080:8080 --env-file .env scamshield:latest

# Google Cloud Run
gcloud run deploy scamshield --source . --port 8080 --region us-central1 --allow-unauthenticated
```

---

## 🗺️ Roadmap

- [ ] **On-Device Small Language Model (SLM)**: Integrate Gemma 2B / Qwen2.5 on-device via MLC-LLM / WebGPU for zero-cloud mobile reasoning.
- [ ] **Real-Time Telecom & Bank Threat Feeds**: Connect verified threat feeds (e.g. Chakshu, Indian Cybercrime Coordination Centre (I4C), PhishTank).
- [ ] **Family Guardian Console**: Multi-device dashboard enabling family administrators to assist elderly relatives with flagged scam escalations.
- [ ] **Voice-Call Scam Shield**: Real-time speech-to-text audio triage detecting digital arrest and extortion patterns during inbound phone calls.

---

## 👤 Author & Acknowledgments

**Author**: [NANDAVELAN](https://github.com/NANDAVELAN/scamshield)

Special thanks to the open-source tools and frameworks powering ScamShield:
- **Google Agent Development Kit (ADK)**: Multi-agent orchestration and schema-enforced LLM agents.
- **Google Gemini**: Multimodal and agentic reasoning engines (Gemini 2.5 Pro & Flash).
- **FastAPI**: Asynchronous web framework and Server-Sent Events infrastructure.
- **TypeSafe AI**: High-velocity structured reflex triage SDK.
- **Ollama**: Local, private on-device LLM runtime.

---

## 📄 License

ScamShield is licensed under the [MIT License](LICENSE).
