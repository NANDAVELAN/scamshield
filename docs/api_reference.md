# 📡 ScamShield API Reference

Base URL: `http://localhost:8080` (or configured `PORT`)

---

## 1. Health Check

### `GET /health`
Returns the operational health and environment status of the ScamShield backend.

**Response (200 OK):**
```json
{
  "status": "ok",
  "env": "local",
  "timestamp": 1773328400.12,
  "active_sse_clients": 1
}
```

---

## 2. Message Analysis

### `POST /analyze`
Analyzes an inbound SMS, email, or WhatsApp message through the reflex triage gate and multi-agent pipeline.

**Request Body (`application/json`):**
```json
{
  "channel": "sms",
  "sender": "+91-98765-43210",
  "subject": "",
  "body": "Dear customer, your account KYC has expired. Update now at http://sbi-kyc-update.in or services will be halted.",
  "urls": ["http://sbi-kyc-update.in"],
  "attachments": []
}
```

**Response (200 OK):**
```json
{
  "incident_id": "INC-A9F21B",
  "triage": {
    "scam_probability": 0.88,
    "scam_type": "fake_kyc",
    "urgency": 4,
    "source": "jev",
    "latency_ms": 78
  },
  "verdict": {
    "risk_score": 88,
    "label": "scam",
    "scam_type": "fake_kyc",
    "evidence": [
      {
        "source_tool": "url_investigator",
        "finding": "Domain sbi-kyc-update.in registered 3 days ago; lookalike of State Bank of India",
        "severity": "high"
      },
      {
        "source_tool": "sender_investigator",
        "finding": "Sender phone number has 14 prior fraud reports",
        "severity": "high"
      }
    ],
    "explanation_en": "High risk fake KYC phishing scam impersonating SBI using a newly registered lookalike domain.",
    "explanation_local": "எஸ்பிஐ வங்கியைப் போல் போலியாக ஆள்மாறாட்டம் செய்து உருவாக்கப்பட்டுள்ள போலி கேஒய்சி மோசடி.",
    "recommended_action": "quarantine"
  },
  "provider_used": "gemini-2.5-pro",
  "cache_hit": false,
  "status": "pending_approval",
  "campaign_id": "CAMP-SBI-KYC-01",
  "score": 88,
  "action": "quarantine",
  "reason": "High risk fake KYC phishing scam impersonating SBI using a newly registered lookalike domain.",
  "evidence": {
    "reflex": "Reflex gate (jev) probability 0.88",
    "url": "Domain sbi-kyc-update.in registered 3 days ago; lookalike of State Bank of India",
    "sender": "Sender phone number has 14 prior fraud reports",
    "attachment": "No attachments"
  }
}
```

---

## 3. Real-Time Execution Streaming

### `GET /analyze/stream`
Server-Sent Events (SSE) stream broadcasting live pipeline execution stages, specialist node activations, provider latencies, and verdicts.

**Stream Event Structure:**
```json
{
  "stage": "investigator",
  "agent": "url_investigator",
  "status": "done",
  "provider": "gemini-2.5-pro",
  "latency_ms": 340,
  "payload": {
    "domain": "sbi-kyc-update.in",
    "risk": "high"
  }
}
```

---

## 4. Incident Management & Human Consent

### `GET /incidents`
Lists all tracked incidents and their execution status.

### `GET /incidents/{incident_id}`
Retrieves full details, evidence trail, and action status for a single incident.

### `POST /incidents/{incident_id}/approve`
Executes the proposed reversible defense action (`quarantine`, `block_sender`, `block_url`).

**Response (200 OK):**
```json
{
  "status": "success",
  "incident_id": "INC-A9F21B",
  "action": "quarantine",
  "details": "Message quarantined successfully in safe isolation vault."
}
```

### `POST /incidents/{incident_id}/reject`
Rejects the proposed defense action. Records rejection in audit log without modifying state.

### `POST /incidents/{incident_id}/undo`
Reverses a previously executed defense action (e.g., releases quarantined message back to user view).

---

## 5. Web Surfaces Mounted

- **Message & Attack Simulator:** `GET /simulator` (or root redirect `GET /`)
- **Phone Application (Web Preview):** `GET /app`
