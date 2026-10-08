"""Incident logging and defense action proposal tools."""
import time
import uuid
from typing import Dict, Any

ALLOWED_ACTIONS = {"none", "warn", "quarantine", "block_sender", "block_url"}

def open_incident(details: Dict[str, Any]) -> Dict[str, Any]:
    """Create a structured incident record for human review and audit tracking.

    Args:
        details: Dictionary containing message details and risk analysis.

    Returns:
        dict: Generated incident ID and status.
    """
    incident_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
    return {
        "status": "success",
        "incident_id": incident_id,
        "created_at": time.time(),
        "status_code": "pending_approval"
    }

def propose_action(action: str, target: str, reason: str) -> Dict[str, Any]:
    """Propose a non-destructive defense action requiring human approval.
    
    CRITICAL POLICY: Agents NEVER execute actions directly. This tool records a PROPOSAL only.
    Permanent deletion is strictly rejected.

    Args:
        action: Proposed defense action (quarantine, block_sender, block_url, warn, none).
        target: Target identifier (e.g. sender email or domain).
        reason: Justification for the action.

    Returns:
        dict: Proposal state with status pending_approval.
    """
    clean_action = action.lower().strip()
    if clean_action not in ALLOWED_ACTIONS:
        clean_action = "warn"

    return {
        "status": "success",
        "proposed_action": clean_action,
        "target": target,
        "reason": reason,
        "approval_required": True,
        "state": "pending_approval"
    }
