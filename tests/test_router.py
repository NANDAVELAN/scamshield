"""Tests for LLM Router, fallback chain, circuit breaker, and verdict cache."""
import pytest
import asyncio
from llm.router import Router, analyze_with_router
from server.cache import verdict_cache
from scamshield_agent.schemas import Verdict

@pytest.fixture
def clean_cache():
    verdict_cache.clear()
    yield
    verdict_cache.clear()

def test_router_fallback_to_rules(clean_cache):
    """When cloud providers are unavailable, router falls back to rules and returns verdict."""
    async def _test():
        test_router = Router()
        # Simulate outage on all cloud providers
        test_router.simulate_outage.add("gemini-pro")
        test_router.simulate_outage.add("gemini-flash")
        test_router.simulate_outage.add("ollama")

        msg = {
            "channel": "gmail",
            "sender": "alerts@sbi-kyc-update.in",
            "subject": "Account suspension notice",
            "body": "Your SBI account is blocked. Click http://sbi-kyc-update.in immediately.",
            "urls": ["http://sbi-kyc-update.in"],
            "attachments": [],
            "headers": {"spf": "fail"}
        }

        provider_used, verdict, cache_hit = await analyze_with_router(test_router, msg)
        assert provider_used == "rules"
        assert not cache_hit
        assert verdict.label in ("scam", "likely_scam")
        assert verdict.risk_score >= 70

    asyncio.run(_test())

def test_router_cache_hit(clean_cache):
    """Second call for identical message must hit cache."""
    async def _test():
        test_router = Router()
        test_router.simulate_outage.add("gemini-pro")
        test_router.simulate_outage.add("gemini-flash")

        msg = {
            "channel": "sms",
            "sender": "+91-90000-12345",
            "subject": "",
            "body": "You won 25 lakh in KBC! Click http://lottery-winner-claim.biz/kbc",
            "urls": ["http://lottery-winner-claim.biz/kbc"],
            "attachments": [],
            "headers": {}
        }

        # First call: cache miss
        p1, v1, hit1 = await analyze_with_router(test_router, msg)
        assert not hit1

        # Second call: cache hit
        p2, v2, hit2 = await analyze_with_router(test_router, msg)
        assert hit2
        assert p2 == p1
        assert v2.risk_score == v1.risk_score

    asyncio.run(_test())

def test_privacy_mode_skips_cloud(clean_cache):
    """Privacy mode must only attempt non-cloud providers and rules."""
    test_router = Router()
    test_router.privacy_mode = True

    chain = list(test_router.chain())
    assert all(not p["cloud"] for p in chain)
    assert any(p["name"] == "ollama" for p in chain)

def test_circuit_breaker_cooldown(clean_cache):
    """Failing provider must have active cooldown."""
    test_router = Router()
    assert "gemini-pro" in [p["name"] for p in test_router.chain()]

    test_router.mark_failed("gemini-pro", Exception("429 Too Many Requests"), cooldown=120)
    assert "gemini-pro" not in [p["name"] for p in test_router.chain()]

    status = test_router.get_status()
    assert not status["providers"]["gemini-pro"]["healthy"]
    assert status["providers"]["gemini-pro"]["error_count"] == 1

def test_router_successful_llm_execution(clean_cache):
    """When a primary LLM succeeds, router returns that provider and stores it in cache."""
    from unittest.mock import patch

    async def _test():
        test_router = Router()
        mock_verdict = Verdict(
            risk_score=92,
            label="scam",
            scam_type="fake_kyc",
            evidence=[],
            explanation_en="LLM detected credential harvest attempt",
            explanation_local="LLM detected credential harvest attempt",
            recommended_action="quarantine"
        )

        with patch("llm.router.run_pipeline", return_value=mock_verdict):
            msg = {
                "channel": "sms",
                "sender": "SBI-ALERT",
                "subject": "",
                "body": "Update PAN at scam link",
                "urls": ["http://fake.com"],
                "attachments": [],
                "headers": {}
            }
            provider, verdict, hit = await analyze_with_router(test_router, msg)
            assert provider == "gemini-pro"
            assert verdict.risk_score == 92
            assert verdict.label == "scam"
            assert not hit

    asyncio.run(_test())
