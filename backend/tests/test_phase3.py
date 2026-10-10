"""Test suite for Phase 3:
- Fallback chain behavior
- Mode switching (rules vs llm vs auto)
- SSE stream log format
"""
import pytest
import asyncio
from backend.schemas import Message, Verdict
from backend.router import analyze_with_agent_router, get_provider_chain

def test_router_mode_rules(monkeypatch):
    """When MODE=rules, router must use rules and report in log."""
    async def _test():
        monkeypatch.setenv("MODE", "rules")
        
        logs = []
        async def capture_log(agent, msg, stage=0):
            logs.append(f"{agent}: {msg}")

        msg = Message(
            channel="whatsapp",
            sender="+91 98xxx 41207",
            body="Congratulations! You won ₹25,00,000 in the KBC lottery. Claim now: kbc-claim.in/win"
        )

        verdict = await analyze_with_agent_router(msg, broadcast_callback=capture_log)
        assert verdict.verdict == "scam"
        assert verdict.mode == "rules"
        assert any("using rules" in l.lower() for l in logs)

    asyncio.run(_test())

def test_router_cascade_to_rules_when_keys_missing(monkeypatch):
    """When cloud keys are missing or invalid, router gracefully cascades to deterministic rules."""
    async def _test():
        monkeypatch.setenv("MODE", "llm")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        logs = []
        async def capture_log(agent, msg, stage=0):
            logs.append(f"{agent}: {msg}")

        msg = Message(
            channel="sms",
            sender="VM-HDFCBK",
            body="Your a/c XX4521 is debited Rs 1,250 at Swiggy. Not you? Call the number on your card."
        )

        verdict = await analyze_with_agent_router(msg, broadcast_callback=capture_log)
        assert verdict.verdict == "safe"
        assert verdict.mode == "rules"
        assert any("using rules" in l.lower() for l in logs)

    asyncio.run(_test())

def test_provider_chain_configuration(monkeypatch):
    """Verify provider chain responds to environment variable keys."""
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-key")

    chain = get_provider_chain()
    names = [p["name"] for p in chain]
    assert "Gemini Pro" in names
    assert "OpenRouter" not in names
    assert "Ollama Local" in names
