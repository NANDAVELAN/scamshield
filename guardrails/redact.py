"""PII redaction utilities for data-minimization before model evaluation."""
import re

PHONE_REGEX = re.compile(r'(?:\+?91[\-\s]?)?[6-9]\d{4}[\-\s]?\d{5}\b')
ACCOUNT_REGEX = re.compile(r'\b(?:\d{4}[\s\-]?){3}\d{4}\b|\b\d{9,18}\b')
EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')

def redact_pii(text: str) -> str:
    """Redact phone numbers, account numbers, and personal identifiers from text."""
    if not text:
        return ""
    
    redacted = text
    # Redact 16-digit card numbers and 9-18 digit account numbers
    redacted = ACCOUNT_REGEX.sub("[ACCOUNT_REDACTED]", redacted)
    # Redact phone numbers
    redacted = PHONE_REGEX.sub("[PHONE_REDACTED]", redacted)
    
    return redacted

def has_raw_pii(text: str) -> bool:
    """Check if string contains unredacted phone numbers or account numbers."""
    if not text:
        return False
    if PHONE_REGEX.search(text):
        return True
    if ACCOUNT_REGEX.search(text):
        return True
    return False
