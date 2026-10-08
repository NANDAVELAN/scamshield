"""Incident opening and non-destructive action proposal tools."""
from typing import Dict, Any

def open_incident(details: Dict[str, Any]) -> Dict[str, Any]:
    """Create a structured incident record for human review and audit tracking.

    Args:
        details: Dictionary containing message details and risk analysis.

    Returns:
        dict: Generated incident ID and status.
    """
    return {
        "status": "success",
        "incident_id": "INC-001",
        "status_code": "pending_approval"
    }

def propose_action(action: str, target: str, reason: str) -> Dict[str, Any]:
    """Propose a non-destructive defense action requiring human approval.

    Args:
        action: Proposed defense action (quarantine, block_sender, block_url, warn, none).
        target: Target identifier (e.g. sender email or domain).
        reason: Justification for the action.

    Returns:
        dict: Proposal state with status pending_approval.
    """
    return {
        "status": "success",
        "proposed_action": action,
        "target": target,
        "reason": reason,
        "approval_required": True,
        "state": "pending_approval"
    }
