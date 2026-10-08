"""Entity extraction and PII redaction tool for ScamShield."""
import json
import os
import re
from typing import Dict, Any, List
from urllib.parse import urlparse
from guardrails.redact import redact_pii

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def _load_brands() -> Dict[str, List[str]]:
    path = os.path.join(DATA_DIR, "brands.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

URL_REGEX = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+', re.IGNORECASE)
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(?:\+?91[\-\s]?)?[6-9]\d{4}[\-\s]?\d{5}\b')

def extract_entities(text: str) -> Dict[str, Any]:
    """Extract entities (URLs, domains, phone numbers, emails, brand names) from message text while redacting sensitive PII.

    Args:
        text: The message body to extract entities from.

    Returns:
        dict: A dictionary containing extracted domains, urls, phones, emails, brands, and redacted text.
    """
    if not text:
        return {
            "status": "success",
            "domains": [],
            "urls": [],
            "phones": [],
            "emails": [],
            "brands": [],
            "redacted_text": ""
        }

    raw_urls = URL_REGEX.findall(text)
    urls = []
    domains = set()
    for u in raw_urls:
        formatted = u if u.startswith("http") else "http://" + u
        urls.append(formatted)
        try:
            parsed = urlparse(formatted)
            netloc = parsed.netloc.lower()
            if ":" in netloc:
                netloc = netloc.split(":")[0]
            if netloc:
                domains.add(netloc)
        except Exception:
            pass

    emails = EMAIL_REGEX.findall(text)
    phones = PHONE_REGEX.findall(text)

    # Detect brand mentions
    brands_data = _load_brands()
    found_brands = []
    text_lower = text.lower()
    for brand in brands_data.keys():
        pattern = r'\b' + re.escape(brand.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found_brands.append(brand)

    # Redact raw PII
    redacted = redact_pii(text)

    return {
        "status": "success",
        "domains": list(domains),
        "urls": urls,
        "phones": list(set(phones)),
        "emails": list(set(emails)),
        "brands": found_brands,
        "redacted_text": redacted
    }
