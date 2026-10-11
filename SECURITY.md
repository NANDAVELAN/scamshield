# Security Policy

## Reporting Security Issues

We take the security and privacy of ScamShield seriously. If you discover a potential security vulnerability, secret exposure, or bypass of our safety guardrails, please disclose it responsibly.

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, report security concerns directly to the project maintainers via email at:  
`security@scamshield.example` (or through GitHub Private Vulnerability Reporting).

Please provide:
- A description of the vulnerability or guardrail bypass.
- Steps to reproduce or proof-of-concept payload.
- Potential impact and recommended mitigations.

We will acknowledge receipt within 48 hours and work with you on a resolution.

---

## Repository Privacy & Credentials Notice

- **No Secrets in Repository**: No real API keys, access tokens, service accounts, or production passwords belong in this repository or its commit history.
- **Untrusted Inbound Data**: All messages submitted to ScamShield are treated as **completely untrusted data**. All defenses and invariants (I1–I8) are enforced deterministically in Python code, not through prompt instructions.
- **Non-Destructive Guarantee**: Agents only propose actions. All code execution runs in `server/executor.py` upon human consent, and no deletion paths exist anywhere in ScamShield.
- **Mock Threat Intelligence**: All domain reputation, sender scores, and blocklist data in `scamshield_agent/data/` are synthetic, offline mock datasets created strictly for evaluation and testing.
