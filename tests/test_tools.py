"""Unit tests for ScamShield investigation tools."""
import pytest
from scamshield_agent.tools.entities import extract_entities
from scamshield_agent.tools.url_tools import check_lookalike, get_domain_age, check_blocklist
from scamshield_agent.tools.sender_tools import get_sender_reputation, check_email_auth
from scamshield_agent.tools.attachment_tools import analyze_attachment
from scamshield_agent.tools.campaign_tools import link_campaign
from scamshield_agent.tools.incident_tools import open_incident, propose_action

def test_extract_entities_and_redact():
    text = "Dear customer, your account 123456789012 at SBI is blocked. Call +91-98765-43210 or visit http://sbi-kyc-update.in"
    res = extract_entities(text)
    assert res["status"] == "success"
    assert "sbi-kyc-update.in" in res["domains"]
    assert "SBI" in res["brands"]
    # PII must be redacted in the text
    assert "123456789012" not in res["redacted_text"]
    assert "+91-98765-43210" not in res["redacted_text"]
    assert "[ACCOUNT_REDACTED]" in res["redacted_text"] or "[PHONE_REDACTED]" in res["redacted_text"]

def test_check_lookalike_detection():
    # Impersonation domain
    fake = check_lookalike("sbi-kyc-update.in")
    assert fake["is_lookalike"] is True
    assert fake["target_brand"] == "SBI"
    assert fake["is_official"] is False

    # Official domain
    official = check_lookalike("sbi.co.in")
    assert official["is_lookalike"] is False
    assert official["is_official"] is True

def test_get_domain_age_mock():
    # New domain
    res_new = get_domain_age("sbi-kyc-update.in")
    assert res_new["is_new"] is True
    assert res_new["age_days"] == 2
    assert res_new["reports"] == 41

    # Established brand domain
    res_old = get_domain_age("sbi.co.in")
    assert res_old["is_new"] is False
    assert res_old["age_days"] == 9000

def test_check_blocklist():
    blocked = check_blocklist("sbi-kyc-update.in")
    assert blocked["is_blocked"] is True

    safe = check_blocklist("google.com")
    assert safe["is_blocked"] is False

def test_sender_reputation_and_auth():
    scam_rep = get_sender_reputation("+91-90000-12345")
    assert scam_rep["is_malicious"] is True
    assert scam_rep["reports"] == 128

    safe_rep = get_sender_reputation("alerts@sbi.co.in")
    assert safe_rep["is_malicious"] is False

    spoofed = check_email_auth({"spf": "fail", "dkim": "none"})
    assert spoofed["is_spoofed"] is True

    valid = check_email_auth({"spf": "pass", "dkim": "pass"})
    assert valid["auth_passed"] is True

def test_analyze_attachment():
    # Double extension executable
    dangerous = analyze_attachment("Invoice.pdf.exe", 150)
    assert dangerous["is_suspicious"] is True
    assert any("double extension" in r.lower() for r in dangerous["reasons"])

    # Legitimate PDF
    safe = analyze_attachment("EBill_Sept2026.pdf", 90)
    assert safe["is_suspicious"] is False

def test_propose_action_never_deletes():
    # Action proposal creates a proposal in pending_approval
    res = propose_action("quarantine", "alerts@bad.com", "Malicious sender")
    assert res["status"] == "success"
    assert res["state"] == "pending_approval"
    assert res["approval_required"] is True

    # If action is delete, it defaults to safe fallback
    res_del = propose_action("delete", "alerts@bad.com", "Malicious sender")
    assert res_del["proposed_action"] != "delete"
