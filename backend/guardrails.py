"""Guardrails harness for input sanitization, prompt injection defense, PII redaction, and output validation."""
import re
import logging
from typing import Dict, Any, Tuple, Optional
from pydantic import ValidationError
from .schemas import Verdict, Evidence

logger = logging.getLogger("scamshield.guardrails")

# Prompt injection signatures
INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior) (instructions|directives|rules)",
    r"disregard (all )?(prior|previous) (prompts|instructions)",
    r"you are now (an? )?(unrestricted|developer mode|dan)",
    r"system prompt:",
    r"output exactly the word 'safe'",
    r"override safety guidelines",
    r"<\|im_start\|>",
    r"\[system\]",
]

# Sensitive PII patterns
PHONE_PATTERN = r"(\+?\d{1,3}[-.\s]?)?(\d{5}[-.\s]\d{5}|\d{10})"
ACCOUNT_PATTERN = r"\b(a/c|acc|account)\s*(no\.?)?\s*([0-9]{4,16}|[xX]{2,8}[0-9]{2,6})\b"
OTP_PATTERN = r"\b(otp|code|pin|password)(\s+is|\s*:)?\s*([0-9]{4,8})\b"
EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

def detect_prompt_injection(text: str) -> Tuple[bool, Optional[str]]:
    """Detects if message text contains prompt injection attempts."""
    if not text:
        return False, None
    for pattern in INJECTION_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return True, f"Prompt injection attempt detected: '{match.group(0)}'"
    return False, None

def redact_pii(text: str) -> str:
    """Redacts phones, account numbers, OTPs, and emails before sending to any cloud LLM."""
    if not text:
        return ""
    
    redacted = text
    # 1. Redact OTPs
    redacted = re.sub(OTP_PATTERN, r"\1\2 [REDACTED_OTP]", redacted, flags=re.IGNORECASE)
    # 2. Redact Emails
    redacted = re.sub(EMAIL_PATTERN, "[REDACTED_EMAIL]", redacted)
    # 3. Redact Account Numbers
    redacted = re.sub(ACCOUNT_PATTERN, r"\1 \2 [REDACTED_ACCOUNT]", redacted, flags=re.IGNORECASE)
    # 4. Redact Phone numbers (avoiding simple short codes)
    redacted = re.sub(r"(\+?\d{1,3}[-.\s]?)(\d{5}[-.\s]\d{5}|\d{10})", "[REDACTED_PHONE]", redacted)
    
    return redacted

def sandbox_url(url: str) -> str:
    """Sanitizes URL string and ensures no executable scheme like file:// or javascript:."""
    if not url:
        return ""
    clean = url.strip()
    if clean.startswith("javascript:") or clean.startswith("data:") or clean.startswith("file:"):
        return "about:blank"
    return clean

def validate_verdict(raw: Any, fallback_builder=None, message=None) -> Verdict:
    """Validates raw dictionary or object against the strict Verdict Pydantic schema.
    If validation fails, falls back gracefully to deterministic rules.
    """
    if isinstance(raw, Verdict):
        return raw
    
    try:
        if isinstance(raw, dict):
            return Verdict.model_validate(raw)
    except ValidationError as e:
        logger.warning(f"Verdict validation error: {e}. Executing safe rules fallback.")
        
    if fallback_builder and message:
        return fallback_builder(message)
        
    # Default fail-closed verdict
    return Verdict(
        verdict="suspicious",
        score=50,
        action="warn",
        reason="Evaluation returned unexpected format; flagged for manual review.",
        evidence=Evidence(reflex="Fallback triggered due to schema mismatch."),
        mode="rules",
        latency_ms=1.0
    )
