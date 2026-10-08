"""Cross-channel campaign clustering tool for ScamShield."""
import hashlib
from typing import Dict, Any

CAMPAIGN_REGISTRY: Dict[str, str] = {}

def link_campaign(sender: str, domain: str = "") -> Dict[str, Any]:
    """Group correlated scam messages across channels (email, SMS, WhatsApp) into unified campaign IDs.

    Args:
        sender: Sender identifier (phone number or email).
        domain: Associated domain extracted from the message.

    Returns:
        dict: Campaign ID, match count, and status.
    """
    clean_sender = sender.lower().strip() if sender else ""
    clean_domain = domain.lower().strip() if domain else ""

    key = clean_domain if clean_domain else clean_sender
    if not key:
        key = "generic_cluster"

    # Deterministic campaign hash
    campaign_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()[:6].upper()
    campaign_id = f"CAMP-{campaign_hash}"

    is_new = key not in CAMPAIGN_REGISTRY
    CAMPAIGN_REGISTRY[key] = campaign_id

    return {
        "status": "success",
        "campaign_id": campaign_id,
        "is_new_campaign": is_new,
        "cluster_key": key
    }
