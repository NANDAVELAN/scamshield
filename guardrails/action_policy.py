"""Layer 4: Action Policy Guardrail.
Enforces non-destructive action policies, approval checks, autonomy dial constraints,
sender protection lists, daily rate caps, and reversibility.
"""
from typing import Dict, Any, List, Optional
import time

ALLOWED_ACTIONS = {"none", "warn", "quarantine", "block_sender", "block_url"}
PROTECTED_SENDERS = {
    "alerts@sbi.co.in",
    "alerts@hdfcbank.net",
    "no-reply@amazon.in",
    "orders@flipkart.com",
    "+91-80123-45678"
}

DAILY_AUTO_CAP = 50

class ActionPolicy:
    def __init__(self):
        self.autonomy_mode = "ask"  # "observe", "ask", "auto_low_risk"
        self.auto_actions_today = 0
        self.last_reset = time.time()
        self.audit_log: List[Dict[str, Any]] = []

    def log_action(self, action_type: str, target: str, status: str, details: Dict[str, Any]):
        inc_id = details.get("incident_id") if isinstance(details, dict) else None
        self.audit_log.append({
            "timestamp": time.time(),
            "action": action_type,
            "incident_id": inc_id or "SYSTEM",
            "target": target,
            "status": status,
            "details": details
        })

    def can_execute(self, action: str, target: str, risk_score: int, evidence_count: int, approved: bool) -> tuple[bool, str]:
        """Check if an action is allowed to execute."""
        # Invariant I1: No permanent delete exists anywhere
        if action.lower() == "delete" or "delete" in action.lower():
            self.log_action(action, target, "blocked_destructive", {"reason": "Delete action strictly forbidden"})
            return False, "Deletion is strictly forbidden by policy"

        if action not in ALLOWED_ACTIONS:
            self.log_action(action, target, "blocked_unknown", {"reason": f"Action '{action}' not in allowlist"})
            return False, f"Action '{action}' is not permitted"

        if action in ("none", "warn"):
            return True, "Action allowed without intervention"

        # Protected senders cannot be quarantined or blocked
        if target.lower() in {s.lower() for s in PROTECTED_SENDERS}:
            self.log_action(action, target, "blocked_protected", {"reason": "Sender is on protected allowlist"})
            return False, "Target is on the protected allowlist"

        # Explicit human approval grants permission
        if approved:
            self.log_action(action, target, "approved_by_human", {"risk_score": risk_score})
            return True, "Approved by human operator"

        # Autonomy check for unapproved actions
        if self.autonomy_mode == "auto_low_risk":
            if self.auto_actions_today >= DAILY_AUTO_CAP:
                return False, "Daily automated action cap reached"
            if risk_score >= 85 and evidence_count >= 2:
                self.auto_actions_today += 1
                self.log_action(action, target, "auto_executed", {"risk_score": risk_score})
                return True, "Auto-executed under auto_low_risk policy"
            return False, "Insufficient confidence or evidence for auto-quarantine"

        # Default: approval required
        return False, "Human approval required"

action_policy = ActionPolicy()
