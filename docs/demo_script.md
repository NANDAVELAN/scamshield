# 🎤 ScamShield Demo Script & Presentation Playbook

> **Tagline:** *"An immune system for your inbox."*  
> **Sub-tagline:** *"Think fast. Think hard. Ask a human."*

---

## 1. Executive Summary & Key Differentiators

Most AI defense prototypes act as basic black boxes: *message in → single LLM call → "scam" label*.
ScamShield introduces **five architectural differentiators**:

| # | Differentiator | Technical Proof |
|---|---|---|
| 1 | **Two speeds of thinking** | Instant reflex triage (<100ms via Jev / Gemini Flash / rules) gates deep multi-agent investigation. |
| 2 | **Explainable by construction** | Every verdict cites the specialized tool that found it (Domain WHOIS, Levenshtein lookalike, SPF/DKIM spoof, double-extension MIME). |
| 3 | **Consent by design** | The agent **only proposes**. Reversible actions are executed only upon explicit operator approval. **Zero destructive deletion paths exist**. |
| 4 | **Resilient Fallback Chain** | Gemini Pro → Gemini Flash → OpenRouter → Local Ollama → Offline Rules Scorer. Guaranteed response even during cloud outages. |
| 5 | **Safety Harness & Invariants** | 8 deterministic safety invariants (I1–I8) asserted continuously against golden and adversarial suites. |

---

## 2. 4-Minute Presentation Arc

| Time | Stage | Action / Speaking Point |
|---|---|---|
| **0:00 - 0:30** | **The Hook** | *"Everyone has received an urgent SMS claiming their bank account or electricity is suspended. Victims have seconds to decide. Traditional spam filters are opaque black boxes that either block silently or fail completely."* |
| **0:30 - 1:15** | **The Immune System Solution** | Present the cognitive architecture: System 1 Reflex Gate (fast defense) + System 2 Deep Agent Investigation + 5-Layer Guardrails + Human Approval Gate. |
| **1:15 - 2:00** | **Act 1: Simulator Attack Run** | Open the Attack Simulator (`http://localhost:8080/simulator`). Select the **Fake SBI KYC Suspension** scenario. Watch the reflex triage flash immediate high-urgency detection, followed by parallel specialist investigator nodes illuminating in real time. |
| **2:00 - 2:45** | **Act 2: Evidence & Human Consent** | Show the synthesized verdict and bilingual explanation (English + Tamil). Highlight the proposed defense action (`quarantine`). Show that the message is sealed/blurred pending human consent. Click **Approve Action**; show the logged execution in the audit trail. |
| **2:45 - 3:30** | **Act 3: Outage Resilience & Reversibility** | Demonstrate action reversibility by clicking **Undo Action**. Explain how the router trips circuit breakers during API failures and falls back automatically to local rules with zero downtime. |
| **3:30 - 4:00** | **Summary & Roadmap** | Show the Evaluation Harness (`python -m harness.run`) proving 100% catch rate on the golden test suite with zero false positives. Conclude: *"Scammers rely on users acting before they think. ScamShield thinks faster, investigates deeper, and always asks for consent."* |

---

## 3. Demo Choreography Checklist

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
