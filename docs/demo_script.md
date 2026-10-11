# 🎬 ScamShield Walkthrough & Live Demonstration Guide

> **Tagline:** *"An immune system for your inbox: Think fast. Think hard. Ask a human."*

---

## 1. Executive Summary & Key Differentiators

Most AI security tools act as basic black boxes: *message in → single LLM call → "scam" label*.
ScamShield introduces **five architectural differentiators**:

| # | Differentiator | Technical Proof |
|---|---|---|
| 1 | **Two speeds of thinking** | Instant reflex triage (<100ms via Jev / Gemini Flash / rules) gates deep multi-agent investigation. |
| 2 | **Explainable by construction** | Every verdict cites the specialized tool that found it (Domain WHOIS, Levenshtein lookalike, SPF/DKIM spoof, double-extension MIME). |
| 3 | **Consent by design** | The agent **only proposes**. Reversible actions are executed only upon explicit operator approval. **Zero destructive deletion paths exist**. |
| 4 | **Resilient Fallback Chain** | Gemini Pro → Gemini Flash → OpenRouter → Local Ollama → Offline Rules Scorer. Guaranteed response even during cloud outages. |
| 5 | **Safety Harness & Invariants** | 8 deterministic safety invariants (I1–I8) asserted continuously against golden and adversarial suites. |

---

## 2. End-to-End Walkthrough Arc

| Stage | Focus Area | Workflow / Architecture Milestone |
|---|---|---|
| **Phase 1: Inbound Intake** | **Threat Interception** | Untrusted inbound messages (SMS, Email, WhatsApp) enter through the input sanitization and PII redaction layer. |
| **Phase 2: Reflex Triage** | **Sub-100ms Gate** | The Reflex Gate (TypeSafe AI / Jev or Gemini Flash structured output) rapidly evaluates threat indicators to bypass heavy computation for benign alerts. |
| **Phase 3: Deep Investigation** | **Simulator Attack Run** | When suspicious signals emerge, Google ADK parallel specialist agents (URL/Domain, Sender/SPF, Attachment/MIME) analyze deep evidence concurrently. |
| **Phase 4: Synthesis & Consent** | **Evidence & Human Gate** | Synthesizer compiles an explainable bilingual verdict (English + regional language) and proposes reversible defense actions (`quarantine`). High-risk content remains sealed pending human approval. |
| **Phase 5: Reversibility & Audit** | **Audit Trail & Undo** | Operators can approve, reject, or undo actions instantly. All decisions are captured in an append-only JSON audit log. |
| **Phase 6: Empirical Verification** | **Invariant Proofs (I1–I8)** | Running `python -m harness.run` programmatically proves zero regressions across the golden and adversarial test suites. |

---

## 3. System Verification & Walkthrough Checklist

- [ ] Backend running locally: `python -m server.main` (or `./start.sh` / `.\start.ps1`) on port `8080`.
- [ ] Message Simulator loaded at `http://localhost:8080/simulator`.
- [ ] Phone web interface accessible at `http://localhost:8080/app`.
- [ ] Sample attacks verified:
  - **Fake SBI KYC Suspension** (`http://sbi-kyc-update.in/login` + `KYC_Verification_Form.pdf.exe`) -> Verdict: Scam (Quarantine proposed).
  - **BESCOM Electricity Power Disconnect** (`http://bescom-bill-pay.click`) -> Verdict: Scam.
  - **Legitimate Amazon Delivery / SBI Salary Alert** -> Verdict: Safe (0% false positive).
- [ ] Action approval and undo cycle tested in Simulator.
- [ ] Safety harness verified: `python -m harness.run` passing all invariants I1–I8.

---

## 4. Frequently Asked Questions (FAQ)

### What if the reflex model is wrong?
The reflex model acts as an initial gate. Low-risk messages bypass heavy multi-agent loops to conserve latency and API costs. Any suspicious indicator automatically escalates to deep investigation. Critical defensive actions always require human confirmation.

### How are false positives prevented?
The evaluation suite benchmarks legitimate transactional messages (e.g. genuine bank credit notices, courier delivery receipts) alongside scam archetypes. The deterministic rules engine requires multiple corroborated threat indicators before escalating risk.

### Is user data exposed to cloud LLMs?
No. The first guardrail layer (`guardrails/redact.py`) automatically strips phone numbers, bank account numbers, Aadhaar/SSN IDs, and credit card numbers before any payload is routed to an external LLM.

### What happens when network or API providers fail?
ScamShield includes an automatic multi-tier fallback chain:
`Gemini 2.5 Pro` → `Gemini 2.5 Flash` → `OpenRouter` → `Local Ollama` → `Deterministic Rules Scorer`.
If all remote services fail, ScamShield falls back to its offline heuristic rules scorer in under 5 milliseconds.
