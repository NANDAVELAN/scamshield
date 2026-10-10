"""Integration test suite for FastAPI backend, /analyze, incidents, and approvals."""
import pytest
from fastapi.testclient import TestClient
from server.main import app
from server.cache import verdict_cache
from server.store import incident_store
from server.executor import executor

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_state():
    verdict_cache.clear()
    yield
    verdict_cache.clear()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data

def test_analyze_scam_message_and_approval_flow():
    """End-to-end flow: Analyze -> Incident Created -> Human Approves -> Quarantined."""
    payload = {
        "channel": "gmail",
        "sender": "alerts@sbi-kyc-update.in",
        "subject": "Urgent: Complete KYC",
        "body": "Dear customer, your account is suspended. Click http://sbi-kyc-update.in/login now.",
        "urls": ["http://sbi-kyc-update.in/login"],
        "attachments": [{"name": "KYC_Form.pdf.exe", "size_kb": 220}],
        "headers": {"spf": "fail"}
    }

    # 1. Analyze message
    resp = client.post("/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    incident_id = data["incident_id"]

    assert incident_id.startswith("INC-")
    assert data["verdict"]["label"] in ("scam", "likely_scam")
    assert data["verdict"]["risk_score"] >= 70
    assert data["status"] == "pending_approval"
    assert data["verdict"]["recommended_action"] == "quarantine"

    # 2. Check incident in store
    inc_resp = client.get(f"/incidents/{incident_id}")
    assert inc_resp.status_code == 200
    inc_data = inc_resp.json()
    assert inc_data["incident_id"] == incident_id
    assert inc_data["status"] == "pending_approval"

    # 3. Human Operator Approves Action
    appr_resp = client.post(f"/incidents/{incident_id}/approve")
    assert appr_resp.status_code == 200
    appr_data = appr_resp.json()
    assert appr_data["status"] == "success"
    assert appr_data["action"] == "quarantine"

    # 4. Verify incident status updated to approved
    inc_after = client.get(f"/incidents/{incident_id}").json()
    assert inc_after["status"] == "approved"
    assert any(q["incident_id"] == incident_id for q in executor.quarantined_items)

    # 5. Undo Action
    undo_resp = client.post(f"/incidents/{incident_id}/undo")
    assert undo_resp.status_code == 200
    assert not any(q["incident_id"] == incident_id for q in executor.quarantined_items)

def test_analyze_legitimate_message():
    """Legitimate messages should get low risk and 'safe' label without quarantine."""
    payload = {
        "channel": "gmail",
        "sender": "alerts@sbi.co.in",
        "subject": "Transaction Alert",
        "body": "INR 500 debited from your account via UPI. Never share your OTP.",
        "urls": [],
        "attachments": [],
        "headers": {"spf": "pass", "dkim": "pass"}
    }

    resp = client.post("/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["verdict"]["label"] == "safe"
    assert data["verdict"]["risk_score"] <= 35
    assert data["verdict"]["recommended_action"] == "none"

def test_simulator_static_ui_and_redirect():
    """Verify Simulator static route and root redirect."""
    root_resp = client.get("/", follow_redirects=False)
    assert root_resp.status_code in (302, 307)
    assert root_resp.headers["location"] == "/simulator"

    sim_resp = client.get("/simulator/")
    assert sim_resp.status_code == 200
    assert "Simulator" in sim_resp.text

def test_analyze_triage_contract_and_safe_serialization():
    """Regression test: Ensure /analyze response guarantees non-null string fields for triage and verdict."""
    payload = {
        "channel": "sms",
        "sender": "VM-SBIINB",
        "body": "Dear SBI Customer, your YONO account is locked. Update KYC immediately or account will be suspended in 24 hours.",
        "urls": ["http://sbi-kyc-update.com/app"],
        "attachments": [{"name": "Yono_Update.apk", "size_kb": 0}]
    }
    resp = client.post("/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Triage contract for frontend rendering
    triage = data.get("triage")
    assert triage is not None
    assert "status" in triage
    assert isinstance(triage["status"], str)
    assert triage["status"].lower() in ("escalated", "passed")
    assert "scam_probability" in triage

    # Verdict contract
    verdict = data.get("verdict")
    assert verdict is not None
    assert isinstance(verdict.get("label"), str)
    assert isinstance(verdict.get("recommended_action"), str)
    assert isinstance(verdict.get("risk_score"), int)

def test_fedex_narcotics_courier_simulation():
    """Verify FedEx illegal narcotics simulation achieves high risk score and quarantine."""
    payload = {
        "channel": "sms",
        "sender": "FEDEX-INDIA",
        "body": "FedEx Alert: Parcel #FDX-99812 detained at Mumbai Customs due to unpaid clearance duty and illegal narcotics. Pay Rs. 2,499 immediately to avoid police seizure: http://fedx-customs-pay.in/release",
        "urls": ["http://fedx-customs-pay.in/release"],
        "attachments": []
    }
    resp = client.post("/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    verdict = data["verdict"]

    assert verdict["risk_score"] >= 80
    assert verdict["label"] in ("scam", "likely_scam")
    assert verdict["recommended_action"] == "quarantine"
    assert len(verdict["evidence"]) >= 3
    # Check for brand lookalike or extortion intelligence
    evidence_tools = [e["source_tool"] for e in verdict["evidence"]]
    assert "check_lookalike" in evidence_tools or "threat_intelligence" in evidence_tools

def test_simulator_and_phone_app_static_endpoints():
    """Verify both Simulator and Phone Application web endpoints resolve properly."""
    # Root redirect
    root_resp = client.get("/", follow_redirects=False)
    assert root_resp.status_code in (307, 302, 200)

    # Simulator static assets
    sim_resp = client.get("/simulator/", follow_redirects=True)
    assert sim_resp.status_code == 200
    assert "ScamShield" in sim_resp.text

    # Phone application static assets
    app_resp = client.get("/app/", follow_redirects=True)
    assert app_resp.status_code == 200
    assert "ScamShield" in app_resp.text

    app_file_resp = client.get("/app/index.html")
    assert app_file_resp.status_code == 200
    assert "ScamShield" in app_file_resp.text



