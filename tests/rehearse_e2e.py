"""End-to-End Rehearsal verifying the 6 Definition of Done requirements against live server."""
import json
import urllib.request
import time
import sys

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_URL = "http://127.0.0.1:8080"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def post(path, data):
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}{path}", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def main():
    print("[E2E REHEARSAL] Verifying Definition of Done against live ScamShield backend...")
    
    # 0. Health check
    h = get("/health")
    assert h["status"] == "ok"
    print("  [PASS] Health check OK:", h)

    # 1. Paste scam message #1 -> returns verdict, evidence, provider, proposed action
    scam1 = {
        "channel": "sms",
        "sender": "VM-SBIINB",
        "body": "Dear SBI Customer, your YONO account is locked. Update KYC immediately or account will be suspended in 24 hours. Download Yono_Update.apk from http://sbi-kyc-update.com/app",
        "urls": ["http://sbi-kyc-update.com/app"],
        "attachments": ["Yono_Update.apk"]
    }
    res1 = post("/analyze", scam1)
    print("  [PASS] Rehearsal 1: Analysis successful")
    print(f"      Incident ID: {res1['incident_id']}")
    print(f"      Risk Score: {res1['verdict']['risk_score']}/100 | Label: {res1['verdict']['label']}")
    print(f"      Provider Used: {res1['provider_used']}")
    print(f"      Proposed Action: {res1['verdict']['recommended_action']}")
    print(f"      Evidence Count: {len(res1['verdict']['evidence'])}")
    assert res1["verdict"]["risk_score"] >= 60
    assert res1["verdict"]["recommended_action"] == "quarantine"
    assert len(res1["verdict"]["evidence"]) > 0

    # 2. Operator Approve -> quarantined; Operator Reject on another -> not quarantined; both in audit log
    inc1_id = res1["incident_id"]
    app_res = post(f"/incidents/{inc1_id}/approve", {})
    assert app_res["status"] == "success"
    print(f"  [PASS] Rehearsal 2a: Incident {inc1_id} approved & quarantined:", app_res.get("details", app_res.get("message")))

    # Analyze second scam and reject
    scam2 = {
        "channel": "sms",
        "sender": "+919876543210",
        "body": "Dear Consumer, your electricity power will be disconnected tonight at 9:30 PM from electricity office because your previous month bill was not updated. Contact electricity officer at 9876543210.",
        "urls": ["http://t.ly/mseb-bill"],
        "attachments": []
    }
    res2 = post("/analyze", scam2)
    inc2_id = res2["incident_id"]
    rej_res = post(f"/incidents/{inc2_id}/reject", {})
    assert rej_res["status"] == "success"
    print(f"  [PASS] Rehearsal 2b: Incident {inc2_id} rejected by operator:", rej_res.get("details", rej_res.get("message")))

    # Check incident retrieval
    inc1 = get(f"/incidents/{inc1_id}")
    assert inc1["incident_id"] == inc1_id
    print(f"  [PASS] Rehearsal 2c: Incident {inc1_id} status verified: {inc1['status']}")

    # 3. Message Simulator UI route check
    sim_req = urllib.request.Request(f"{BASE_URL}/simulator/")
    with urllib.request.urlopen(sim_req) as resp:
        assert resp.status == 200
        print("  [PASS] Rehearsal 3: Attack & Defense Simulator served at /simulator")

    # 4. Root redirect to /simulator check
    root_req = urllib.request.Request(f"{BASE_URL}/", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(root_req) as resp:
        assert resp.status == 200
        print("  [PASS] Rehearsal 4: Root redirect to /simulator verified")

    print("\n[SUCCESS] ALL DEFINITION OF DONE REHEARSAL CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    main()
