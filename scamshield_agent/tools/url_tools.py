"""URL and domain investigation tools for ScamShield."""
import json
import os
import re
from typing import Dict, Any, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

def _load_json(filename: str) -> Dict[str, Any]:
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

HOMOGLYPHS = [
    ("rn", "m"),
    ("0", "o"),
    ("1", "l"),
    ("vv", "w"),
    ("cl", "d"),
    ("@", "a"),
    ("$", "s"),
    ("3", "e"),
    ("5", "s"),
]

def normalize_homoglyphs(text: str) -> str:
    """Normalize common homoglyphs and character substitutions."""
    result = text.lower()
    for src, dst in HOMOGLYPHS:
        result = result.replace(src, dst)
    return result

def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def check_lookalike(domain: str) -> Dict[str, Any]:
    """Check if a domain is a homoglyph or lookalike impersonating a known brand.

    Args:
        domain: The domain name to inspect.

    Returns:
        dict: Inspection outcome with target brand, similarity details, and status.
    """
    clean_domain = domain.lower().strip()
    if "/" in clean_domain:
        clean_domain = clean_domain.split("/")[0]

    brands_data = _load_json("brands.json")
    normalized_domain = normalize_homoglyphs(clean_domain)

    # First check: Is this domain an exact authorized brand domain?
    for brand, official_domains in brands_data.items():
        if clean_domain in [d.lower() for d in official_domains]:
            return {
                "status": "success",
                "domain": clean_domain,
                "is_lookalike": False,
                "is_official": True,
                "target_brand": brand,
                "similarity_score": 1.0,
                "details": "Authorized official brand domain"
            }

    # Second check: Does domain contain a brand name or homoglyph variation?
    # e.g., 'sbi-kyc-update.in', 'paytm-refund-support.online'
    for brand, official_domains in brands_data.items():
        brand_norm = brand.lower()
        if brand_norm in normalized_domain or brand_norm in clean_domain:
            return {
                "status": "success",
                "domain": clean_domain,
                "is_lookalike": True,
                "is_official": False,
                "target_brand": brand,
                "similarity_score": 0.95,
                "details": f"Unauthorized domain containing brand name '{brand}'"
            }

        # Check edit distance against official root domains
        for off_dom in official_domains:
            off_sld = off_dom.split(".")[0]
            clean_sld = clean_domain.split(".")[0]
            dist = levenshtein_distance(clean_sld, off_sld)
            if 0 < dist <= 2 and len(off_sld) >= 4:
                return {
                    "status": "success",
                    "domain": clean_domain,
                    "is_lookalike": True,
                    "is_official": False,
                    "target_brand": brand,
                    "similarity_score": 1.0 - (dist / max(len(clean_sld), len(off_sld))),
                    "details": f"Lookalike domain closely matching official domain '{off_dom}' (distance={dist})"
                }

    return {
        "status": "success",
        "domain": clean_domain,
        "is_lookalike": False,
        "is_official": False,
        "target_brand": None,
        "similarity_score": 0.0,
        "details": "No known brand lookalike detected"
    }

def get_domain_age(domain: str) -> Dict[str, Any]:
    """Retrieve domain registration age and risk tag from mock WHOIS reputation.

    Args:
        domain: The domain name to check.

    Returns:
        dict: Domain age in days, reputation tag, reports count, and status.
    """
    clean_domain = domain.lower().strip()
    if "/" in clean_domain:
        clean_domain = clean_domain.split("/")[0]

    reputation_db = _load_json("domain_reputation.json")
    if clean_domain in reputation_db:
        entry = reputation_db[clean_domain]
        return {
            "status": "success",
            "domain": clean_domain,
            "age_days": entry.get("age_days", 365),
            "tag": entry.get("tag", "unknown"),
            "reports": entry.get("reports", 0),
            "is_new": entry.get("age_days", 365) < 30
        }

    # Default for unlisted domains
    return {
        "status": "success",
        "domain": clean_domain,
        "age_days": 180,
        "tag": "unregistered_or_neutral",
        "reports": 0,
        "is_new": False
    }

def check_blocklist(target: str) -> Dict[str, Any]:
    """Check if a domain, URL, or sender is present in known threat blocklists.

    Args:
        target: The domain, URL, or sender to query.

    Returns:
        dict: Blocklist match status and risk reason.
    """
    clean_target = target.lower().strip()
    blocklist = _load_json("blocklist.json")

    blocked_domains = [d.lower() for d in blocklist.get("domains", [])]
    blocked_senders = [s.lower() for s in blocklist.get("senders", [])]

    # Check domains
    for bd in blocked_domains:
        if bd in clean_target:
            return {
                "status": "success",
                "target": target,
                "is_blocked": True,
                "reason": f"Matched blocked malicious domain '{bd}'"
            }

    # Check senders
    for bs in blocked_senders:
        if bs in clean_target:
            return {
                "status": "success",
                "target": target,
                "is_blocked": True,
                "reason": f"Matched blocked scam sender '{bs}'"
            }

    return {
        "status": "success",
        "target": target,
        "is_blocked": False,
        "reason": None
    }
