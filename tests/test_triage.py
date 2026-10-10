"""Test suite for reflex triage and rules-based scoring on all 20 sample messages."""
import json
import os
import pytest
from triage.rules import score_rules, rules_only_verdict

SAMPLES_PATH = os.path.join(os.path.dirname(__file__), "sample_messages.json")

def load_sample_messages():
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_sample_messages_count():
    messages = load_sample_messages()
    assert len(messages) >= 20
    scams = [m for m in messages if m["type"] == "scam"]
    legit = [m for m in messages if m["type"] == "legitimate"]
    assert len(scams) >= 12
    assert len(legit) >= 8

def test_triage_rules_on_all_samples():
    messages = load_sample_messages()
    scam_count = 0
    scam_detected = 0
    legit_count = 0
    false_positives = 0

    for msg in messages:
        triage = score_rules(msg)
        verdict = rules_only_verdict(msg)

        assert 0.0 <= triage.scam_probability <= 1.0
        assert 0 <= triage.urgency <= 10
        assert triage.source == "rules"
        assert triage.latency_ms >= 0

        if msg["type"] == "scam":
            scam_count += 1
            if triage.scam_probability >= 0.40 or verdict.label in ("scam", "likely_scam", "suspicious"):
                scam_detected += 1
            else:
                pytest.fail(f"Scam missed: {msg['id']} ({msg['scam_type']}) got prob={triage.scam_probability}, label={verdict.label}")
        elif msg["type"] == "legitimate":
            legit_count += 1
            if triage.scam_probability > 0.40 or verdict.label in ("scam", "likely_scam"):
                false_positives += 1
                pytest.fail(f"False positive on legitimate message: {msg['id']} got prob={triage.scam_probability}, label={verdict.label}")

    catch_rate = (scam_detected / scam_count) * 100
    fp_rate = (false_positives / legit_count) * 100

    print(f"\nTriage Performance: Catch Rate = {catch_rate:.1f}%, False Positives = {fp_rate:.1f}%")
    assert catch_rate >= 90.0
    assert fp_rate == 0.0

def test_rules_only_verdict_structure():
    messages = load_sample_messages()
    sample_scam = messages[0]
    verdict = rules_only_verdict(sample_scam)
    assert verdict.risk_score >= 70
    assert verdict.label == "scam"
    assert len(verdict.evidence) > 0
    assert "hxxp" in verdict.explanation_en or "http" not in verdict.explanation_en

def test_gemini_flash_llm_decision_flow(monkeypatch):
    """Test that Gemini Flash LLM properly formats and returns TriageResult."""
    import asyncio
    from unittest.mock import MagicMock, patch
    from triage.jev_client import _call_gemini_flash_json

    async def _test():
        monkeypatch.setenv("GOOGLE_API_KEY", "mock-test-key-12345")

        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "scam_probability": 0.95,
            "scam_type": "fake_kyc",
            "urgency": 9,
            "impersonates_brand": 0.92
        })

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with patch("google.genai.Client", return_value=mock_client):
            sample = {
                "sender": "alerts@sbi-kyc.in",
                "subject": "KYC Expired",
                "body": "Update your SBI KYC immediately or your account will be suspended."
            }
            result = await _call_gemini_flash_json(sample)
            assert result.source == "gemini_flash"
            assert result.scam_probability == 0.95
            assert result.scam_type == "fake_kyc"
            assert result.urgency == 9
            assert result.status == "escalated"

    asyncio.run(_test())

def test_typesafe_jev_decision_flow(monkeypatch):
    """Test that TypeSafe AI Jev System One properly parses answers from @typesafe-ai/sdk spec."""
    import asyncio
    from unittest.mock import MagicMock, AsyncMock, patch
    from triage.jev_client import _call_jev

    async def _test():
        monkeypatch.setenv("TYPESAFE_API_KEY", "mock-typesafe-key-12345")
        monkeypatch.setenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "answers": {
                "is_scam": {"noul": 0.96},
                "scam_type": {"choice": "bill_disconnect"},
                "urgency": {"score": 8},
                "impersonates_brand": {"noul": 0.88}
            },
            "model": "jev-latest"
        }

        mock_http = MagicMock()
        mock_http.post = AsyncMock(return_value=mock_resp)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_http):
            sample = {
                "sender": "Electricity Dept",
                "body": "Dear consumer, your electricity will be disconnected tonight. Pay immediately."
            }
            res = await _call_jev(sample)
            assert res.source == "jev"
            assert res.scam_probability == 0.96
            assert res.scam_type == "bill_disconnect"
            assert res.urgency == 8
            assert res.impersonates_brand == 0.88
            assert res.status == "escalated"

    asyncio.run(_test())

def test_quick_triage_fallback_cascade_when_typesafe_fails(monkeypatch):
    """Test that quick_triage cascades safely to rules when TypeSafe returns 401 or fails."""
    import asyncio
    from unittest.mock import MagicMock, AsyncMock, patch
    from triage.jev_client import quick_triage

    async def _test():
        monkeypatch.setenv("TYPESAFE_API_KEY", "invalid-key")
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        # Mock TypeSafe returning 401 Unauthorized
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Cannot authenticate with the server"

        mock_http = MagicMock()
        mock_http.post = AsyncMock(return_value=mock_resp)
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_http):
            sample = {
                "sender": "SBI-ALERT",
                "body": "Your account is blocked. Update KYC at http://sbi-fake.in now"
            }
            res = await quick_triage(sample)
            # Should have cascaded cleanly to rules without crashing!
            assert res.source == "rules"
            assert res.scam_probability >= 0.5
            assert res.status == "escalated"

    asyncio.run(_test())

