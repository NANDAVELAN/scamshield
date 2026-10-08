"""Jev Quick-Triage reflex client with Gemini Flash JSON and deterministic rules fallback."""
import asyncio
import os
import time
import json
import logging
from typing import Dict, Any, Optional
import httpx
from scamshield_agent.schemas import TriageResult
from triage.rules import score_rules

logger = logging.getLogger("scamshield.triage")

# Jev System One questions per README section 9
JEV_QUESTIONS = [
    {"id": "is_scam", "question": "Is this message a scam?", "type": "probability"},
    {"id": "scam_type", "question": "Which scam type?", "type": "choice",
     "options": ["fake_kyc", "upi_refund", "courier", "bill_disconnect", "job_offer", "digital_arrest", "lottery", "otp_request", "other", "none"]},
    {"id": "urgency", "question": "How urgent/threatening is the language?", "type": "ordinal_0_10"},
    {"id": "impersonates_brand", "question": "Does it impersonate a known brand or authority?", "type": "probability"}
]

async def _call_jev(message: Dict[str, Any]) -> TriageResult:
    """Attempt TypeSafe AI Jev System One decision model."""
    jev_key = os.getenv("JEV_API_KEY", "")
    jev_url = os.getenv("JEV_BASE_URL", "")

    if not jev_key or not jev_url or jev_key == "your_jev_api_key_here":
        raise ConnectionError("Jev API key or base URL not configured")

    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=3.0) as client:
        resp = await client.post(
            f"{jev_url.rstrip('/')}/triage",
            headers={"Authorization": f"Bearer {jev_key}", "Content-Type": "application/json"},
            json={
                "text": f"{message.get('subject', '')} {message.get('body', '')}",
                "questions": JEV_QUESTIONS
            }
        )
        if resp.status_code != 200:
            raise RuntimeError(f"Jev API returned HTTP {resp.status_code}")
        data = resp.json()

    latency_ms = max(1, int((time.perf_counter() - t0) * 1000))
    return TriageResult(
        scam_probability=data.get("is_scam_probability", 0.5),
        scam_type=data.get("scam_type", "other"),
        urgency=int(data.get("urgency_score", 5)),
        impersonates_brand=data.get("impersonates_brand_probability", 0.0),
        source="jev",
        latency_ms=latency_ms
    )

async def _call_gemini_flash_json(message: Dict[str, Any]) -> TriageResult:
    """Fallback Tier 2: Gemini Flash with structured JSON schema answering the 4 questions."""
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ConnectionError("GOOGLE_API_KEY not configured or is placeholder")

    t0 = time.perf_counter()
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    prompt = (
        "Answer these 4 questions for the following incoming message:\n"
        "1. scam_probability (float 0.0 to 1.0)\n"
        "2. scam_type (one of: fake_kyc, upi_refund, courier, bill_disconnect, job_offer, digital_arrest, lottery, otp_request, other, none)\n"
        "3. urgency (integer 0 to 10)\n"
        "4. impersonates_brand (float 0.0 to 1.0)\n\n"
        f"Sender: {message.get('sender')}\n"
        f"Subject: {message.get('subject')}\n"
        f"Body: {message.get('body')}\n"
    )

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TriageResult
        )
    )

    parsed = json.loads(response.text)
    latency_ms = max(1, int((time.perf_counter() - t0) * 1000))

    return TriageResult(
        scam_probability=parsed.get("scam_probability", 0.5),
        scam_type=parsed.get("scam_type", "none"),
        urgency=int(parsed.get("urgency", 0)),
        impersonates_brand=parsed.get("impersonates_brand", 0.0),
        source="gemini_flash",
        latency_ms=latency_ms
    )

async def _call_rules(message: Dict[str, Any]) -> TriageResult:
    """Fallback Tier 3: Deterministic regex and mock-reputation rules."""
    return score_rules(message)

async def quick_triage(message: Dict[str, Any]) -> TriageResult:
    """Fast reflex triage adhering to the fixed interface: Jev -> Gemini Flash JSON -> rules.
    
    3-second timeout per backend. Rules never fail.
    """
    for backend, name in [
        (_call_jev, "jev"),
        (_call_gemini_flash_json, "gemini_flash"),
        (_call_rules, "rules")
    ]:
        try:
            result = await asyncio.wait_for(backend(message), timeout=3.0)
            return result
        except Exception as e:
            logger.info(f"Reflex backend '{name}' bypassed: {e}")
            continue

    # Absolute fallback
    return score_rules(message)
