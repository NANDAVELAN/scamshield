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

# TypeSafe System One questions per official @typesafe-ai/sdk spec
TYPESAFE_QUESTIONS = {
    "is_scam": {"type": "noul", "instructions": "Is this message a scam, phishing attempt, or fraudulent lure?"},
    "scam_type": {
        "type": "choice",
        "instructions": "Which scam category best matches this message?",
        "criteria": {
            "fake_kyc": None,
            "upi_refund": None,
            "courier": None,
            "bill_disconnect": None,
            "job_offer": None,
            "digital_arrest": None,
            "lottery": None,
            "otp_request": None,
            "illegal_narcotics": None,
            "other": None,
            "none": None
        }
    },
    "urgency": {
        "type": "score",
        "instructions": "Rate the level of urgency or coercive pressure from 0 to 10",
        "criteria": [None] * 11
    },
    "impersonates_brand": {"type": "noul", "instructions": "Does the message impersonate a known bank, government body, or recognized brand?"}
}

async def _call_jev(message: Dict[str, Any]) -> TriageResult:
    """Attempt TypeSafe AI Jev System One decision model using official @typesafe-ai/sdk API spec."""
    api_key = (os.getenv("TYPESAFE_API_KEY") or os.getenv("JEV_API_KEY") or "").strip()
    base_url = (os.getenv("TYPESAFE_BASE_URL") or os.getenv("JEV_BASE_URL") or "https://api.typesafe.ai").rstrip("/")

    if not api_key or api_key in ("your_typesafe_api_key_here", "your_jev_api_key_here"):
        raise ConnectionError("TypeSafe API key not configured or set to placeholder")

    t0 = time.perf_counter()
    endpoint = f"{base_url}/v1/systemone" if not base_url.endswith("/v1") else f"{base_url}/systemone"
    
    text_content = f"Channel: {message.get('channel', 'notification')} | Sender: {message.get('sender', '')} | Subject: {message.get('subject', '')} | Body: {message.get('body', '')}"

    payload = {
        "state": text_content,
        "questions": TYPESAFE_QUESTIONS,
        "model": os.getenv("TYPESAFE_MODEL", "jev-latest")
    }

    async with httpx.AsyncClient(timeout=3.0) as client:
        resp = await client.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "typesafe-sdk/0.6.0"
            },
            json=payload
        )
        if resp.status_code != 200:
            raise RuntimeError(f"TypeSafe API returned HTTP {resp.status_code}: {resp.text[:120]}")
        data = resp.json()

    latency_ms = max(1, int((time.perf_counter() - t0) * 1000))
    answers = data.get("answers", {})

    # Extract typed answers from TypeSafe System One format
    is_scam_data = answers.get("is_scam", {})
    prob = float(is_scam_data.get("noul", data.get("is_scam_probability", 0.5)))

    scam_type_data = answers.get("scam_type", {})
    scam_type = scam_type_data.get("choice", data.get("scam_type", "other"))

    urgency_data = answers.get("urgency", {})
    urgency = int(urgency_data.get("score", data.get("urgency_score", 5)))

    brand_data = answers.get("impersonates_brand", {})
    impersonates_brand = float(brand_data.get("noul", data.get("impersonates_brand_probability", 0.0)))

    return TriageResult(
        scam_probability=prob,
        scam_type=scam_type,
        urgency=urgency,
        impersonates_brand=impersonates_brand,
        source="jev",
        latency_ms=latency_ms,
        status="escalated" if prob >= 0.2 else "passed",
        reason=f"TypeSafe Jev classified as {scam_type} (p={prob:.2f})"
    )

async def _call_gemini_flash_json(message: Dict[str, Any]) -> TriageResult:
    """Fallback Tier 2: Gemini Flash with structured JSON schema answering the 4 questions."""
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ConnectionError("GOOGLE_API_KEY not configured or is placeholder")

    t0 = time.perf_counter()
    from google import genai
    from google.genai import types
    from pydantic import BaseModel, Field

    class GeminiTriageResponse(BaseModel):
        scam_probability: float = Field(ge=0.0, le=1.0)
        scam_type: str
        urgency: int = Field(ge=0, le=10)
        impersonates_brand: float = Field(ge=0.0, le=1.0)

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
            response_schema=GeminiTriageResponse
        )
    )

    parsed = json.loads(response.text)
    latency_ms = max(1, int((time.perf_counter() - t0) * 1000))

    prob = float(parsed.get("scam_probability", 0.5))
    return TriageResult(
        scam_probability=prob,
        scam_type=parsed.get("scam_type", "none"),
        urgency=int(parsed.get("urgency", 0)),
        impersonates_brand=float(parsed.get("impersonates_brand", 0.0)),
        source="gemini_flash",
        latency_ms=latency_ms,
        status="escalated" if prob >= 0.2 else "passed",
        reason=f"Gemini Flash detected {parsed.get('scam_type', 'none')}"
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
