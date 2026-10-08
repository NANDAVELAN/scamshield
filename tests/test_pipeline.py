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

def test_control_endpoints():
    """Verify Control Center status, provider override, and autonomy settings."""
    # State check
    st_resp = client.get("/control/state")
    assert st_resp.status_code == 200
    state = st_resp.json()
    assert "providers" in state
    assert "thresholds" in state

    # Provider override
    prov_resp = client.post("/control/provider", json={"force": "ollama", "simulate_outage": ["gemini-pro"]})
    assert prov_resp.status_code == 200

    # Reset provider override
    client.post("/control/provider", json={"force": "", "simulate_outage": []})

    # Mode update
    mode_resp = client.post("/control/mode", json={"autonomy": "auto_low_risk", "privacy": False})
    assert mode_resp.status_code == 200
    assert mode_resp.json()["mode"]["autonomy"] == "auto_low_risk"

    # Reset mode
    client.post("/control/mode", json={"autonomy": "ask", "privacy": False})
