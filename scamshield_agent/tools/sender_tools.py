"""Sender reputation and email authentication inspection tools."""
import json
import os
from typing import Dict, Any

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def _load_sender_db() -> Dict[str, Any]:
    path = os.path.join(DATA_DIR, "sender_reputation.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def get_sender_reputation(sender: str) -> Dict[str, Any]:
    """Retrieve community fraud reports and reputation status for a sender address or phone number.

    Args:
        sender: The sender phone number or email address.

    Returns:
        dict: Fraud reports count, risk tag, and status.
    """
    clean_sender = sender.lower().strip()
    db = _load_sender_db()

    import re
    digits_clean = re.sub(r"\D", "", clean_sender)

    # Exact, substring, or normalized phone digit match
    for s_key, data in db.items():
        digits_key = re.sub(r"\D", "", s_key)
        phone_match = (len(digits_key) >= 10 and len(digits_clean) >= 10 and digits_key[-10:] == digits_clean[-10:])
        if s_key.lower() == clean_sender or clean_sender in s_key.lower() or s_key.lower() in clean_sender or phone_match:
            return {
                "status": "success",
                "sender": sender,
                "reports": data.get("reports", 0),
                "tag": data.get("tag", "unknown"),
                "is_malicious": data.get("reports", 0) > 10 or "scam" in data.get("tag", "") or "phishing" in data.get("tag", "") or "spoof" in data.get("tag", "")
            }


    return {
        "status": "success",
        "sender": sender,
        "reports": 0,
        "tag": "unreported_neutral",
        "is_malicious": False
    }

def check_email_auth(headers: Dict[str, str]) -> Dict[str, Any]:
    """Check SPF and DKIM email authentication headers for spoofing.

    Args:
        headers: Dictionary of email headers including spf and dkim.

    Returns:
        dict: Authentication evaluation, spoofing risk, and status.
    """
    if not isinstance(headers, dict):
        headers = {}

    spf = headers.get("spf", "none").lower()
    dkim = headers.get("dkim", "none").lower()

    is_spoofed = (spf in ("fail", "softfail")) or (dkim == "fail")
    auth_passed = (spf == "pass") and (dkim == "pass")

    return {
        "status": "success",
        "spf": spf,
        "dkim": dkim,
        "is_spoofed": is_spoofed,
        "auth_passed": auth_passed,
        "details": "Authentication failed or missing" if is_spoofed else ("Verified SPF and DKIM" if auth_passed else "Neutral")
    }
