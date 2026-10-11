# Contributing to ScamShield

Thank you for your interest in contributing to ScamShield! We welcome contributions that improve safety, expand detector rules, and strengthen scam defenses.

For in-depth architectural constraints, coding rules, and tool guidelines, see [docs/development.md](docs/development.md) and [AGENTS.md](AGENTS.md).

---

## 1. Development Principles & Code of Conduct

1. **Safety First**:
   - ScamShield is decision support for human protection. Agents only PROPOSE actions.
   - **Zero permanent deletions**: All defensive mitigations must remain reversible (`quarantine`, `block_sender`, `undo`).
   - All sample messages must use synthetic, non-resolving domains and fictionalized test numbers.
2. **Privacy Guarantees**:
   - Never commit API keys, personal tokens, or live credentials.
   - Never use real personal phone numbers, emails, or personal message transcripts in test datasets.
   - All inbound texts must pass through `guardrails/redact.py` before any model exposure.
3. **Evidence-Driven Reasoning**:
   - Any new tool or detection heuristic must return structured evidence and full docstrings.
   - Always run the evaluation harness to verify that invariants I1–I8 remain unbroken.

---

## 2. Setup & Testing Workflow

1. **Clone the repository and set up environment**:
   ```bash
   git clone https://github.com/your-username/scamshield.git
   cd scamshield
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   cp .env.example .env
   ```

2. **Run tests before submitting PR**:
   ```bash
   # Run unit and integration tests
   pytest

   # Run full safety and adversarial invariant harness
   python -m harness.run
   ```

3. **Submitting Changes**:
   - Create a feature branch: `git checkout -b feature/my-enhancement`.
   - Ensure `git diff` contains no secrets or unintended files.
   - Submit a pull request with a clear description of changes and test results.
