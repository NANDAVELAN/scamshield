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
