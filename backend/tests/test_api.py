"""Test FastAPI endpoints for ScamShield."""
import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "ScamShield"
    assert "mode" in data

def test_analyze_endpoint():
    payload = {
        "channel": "whatsapp",
        "sender": "+91 98xxx 41207",
        "body": "Congratulations! You won ₹25,00,000 in the KBC lottery. Claim now: kbc-claim.in/win",
        "urls": ["kbc-claim.in/win"],
        "attachments": [],
        "headers": {}
    }
    resp = client.post("/analyze", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["verdict"] == "scam"
    assert data["score"] >= 80
    assert data["action"] == "block"
    assert "evidence" in data
    assert data["evidence"]["reflex"] is not None
    assert data["latency_ms"] > 0
