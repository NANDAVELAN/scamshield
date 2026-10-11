# 🛠️ ScamShield Developer Guide

This guide outlines architecture constraints, local development workflows, coding standards, and testing procedures for contributors and engineers working on ScamShield.

---

## 1. Architectural Invariants

ScamShield is engineered with strict mathematical and architectural constraints:

1. **Non-Destructive Invariant (I1)**:
   - Agents never possess deletion privileges.
   - All defensive mitigations are reversible: `quarantine`, `block_sender`, `block_url`, and `undo`.
   - Never write code paths that call `os.remove`, `unlink`, or SQL `DELETE` on user data.

2. **Mandatory Human Consent (I2)**:
   - The agent graph **only proposes** defense actions.
   - Execution lives strictly in `server/executor.py` upon explicit operator approval (`approved=True`).

3. **Grounded Evidence (I3)**:
   - Every piece of evidence cited in a `Verdict` must trace back to a specialized tool that was actually executed during that run.

4. **Fail-Closed Resiliency (I4)**:
   - Any upstream timeout, provider crash, or malformed response must yield `needs_review` or suspicious—never an unverified `safe`.

5. **PII Masking (I5)**:
   - Inbound text must pass through `guardrails/redact.py` to scrub mobile numbers, bank accounts, and payment credentials before reaching any external model.

6. **Prompt Injection Resistance (I6)**:
   - Inbound text is treated as untrusted data.
   - Injection payloads must never lower threat scores or bypass guardrail interceptors.

---

## 2. Setting Up the Local Environment

```bash
# 1. Clone the repository
git clone https://github.com/NANDAVELAN/scamshield.git
cd scamshield

# 2. Initialize Python virtual environment (Python 3.11 recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Copy configuration template
cp .env.example .env       # Windows: copy .env.example .env
```

---

## 3. Running Services

### Launch Backend Server
```bash
# Using Makefile
make run

# Or directly with Uvicorn
python -m uvicorn server.main:app --host 127.0.0.1 --port 8080 --reload
```

### Access Local Interfaces
- **Simulator**: [http://127.0.0.1:8080/simulator](http://127.0.0.1:8080/simulator)
- **Phone App Web Preview**: [http://127.0.0.1:8080/app](http://127.0.0.1:8080/app)
- **Swagger API Docs**: [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)

---

## 4. Testing & Invariant Verification

ScamShield mandates continuous programmatic testing before committing changes:

```bash
# 1. Run unit and integration tests (28 tests)
pytest

# 2. Run the Safety & Invariants Evaluation Harness
python -m harness.run

# 3. Run frontend safeguard assertions
node tests/test_frontend_safeguards.js

# 4. Run end-to-end server verification
python tests/verify_e2e.py
```

### Adding New Tools
- Tool definitions live in `scamshield_agent/tools/`.
- Every tool must be a typed function with full docstrings, returning a dictionary with a `status` key.
- Tools must operate exclusively against local sandboxed datasets in `scamshield_agent/data/`; never make unauthenticated live web requests.
- All new tools must be registered in `scamshield_agent/agent.py` and have unit tests in `tests/test_tools.py`.
