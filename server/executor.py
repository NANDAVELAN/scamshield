"""Non-destructive defense action executor for ScamShield.

CRITICAL ARCHITECTURAL CONSTRAINTS:
1. No permanent delete exists anywhere in this codebase.
2. Agents only PROPOSE; execution lives here and requires human approval unless autonomy dial permits.
3. Every executed action is reversible (with full undo capability).
4. All executions are permanently recorded in the append-only audit log.
"""
import time
import logging
from typing import Dict, Any, List, Optional
from guardrails.action_policy import action_policy
from .store import incident_store

logger = logging.getLogger("scamshield.executor")

class ActionExecutor:
    def __init__(self):
        self.quarantined_items: List[Dict[str, Any]] = []
        self.blocked_senders: set = set()
        self.blocked_urls: set = set()
        self.execution_history: List[Dict[str, Any]] = []

    def execute_incident_action(
        self,
        incident_id: str,
        approved: bool = True,
        actor: str = "human_operator"
    ) -> Dict[str, Any]:
        """Execute the proposed action for an incident if permitted by safety policy."""
        incident = incident_store.get(incident_id)
        if not incident:
            return {"status": "error", "message": f"Incident '{incident_id}' not found"}

        action = incident.proposed_action
        target = incident.sender if action in ("block_sender", "quarantine") else (
            incident.urls[0] if incident.urls else incident.sender
        )

        risk_score = incident.verdict.risk_score if incident.verdict else 50
        evidence_count = len(incident.verdict.evidence) if incident.verdict else 0

        # Safety policy validation
        can_run, reason = action_policy.can_execute(
            action=action,
            target=target,
            risk_score=risk_score,
            evidence_count=evidence_count,
            approved=approved
        )

        if not can_run:
            logger.warning(f"Action '{action}' blocked for incident {incident_id}: {reason}")
            return {
                "status": "blocked",
                "incident_id": incident_id,
                "action": action,
                "reason": reason
            }

        # Dispatch plain code execution (reversible)
        record = {
            "timestamp": time.time(),
            "incident_id": incident_id,
            "action": action,
            "target": target,
            "actor": actor,
            "undone": False
        }

        if action == "quarantine":
            self.quarantined_items.append({
                "incident_id": incident_id,
                "target": target,
                "channel": incident.channel,
                "timestamp": time.time()
            })
            incident_store.update_status(incident_id, "approved", actor=actor)
            record["result"] = "Message quarantined in isolated review vault"

        elif action == "block_sender":
            self.blocked_senders.add(target.lower())
            incident_store.update_status(incident_id, "approved", actor=actor)
            record["result"] = f"Sender '{target}' added to local session blocklist"

        elif action == "block_url":
            self.blocked_urls.add(target.lower())
            incident_store.update_status(incident_id, "approved", actor=actor)
            record["result"] = f"URL/Domain '{target}' added to protective blocking filter"

        elif action in ("warn", "none"):
            incident_store.update_status(incident_id, "approved", actor=actor)
            record["result"] = "Warning noted; no active restriction applied"

        self.execution_history.append(record)
        action_policy.log_action(action, target, "executed", record)

        return {
            "status": "success",
            "incident_id": incident_id,
            "action": action,
            "target": target,
            "details": record["result"]
        }

    def reject_incident_action(self, incident_id: str, actor: str = "human_operator") -> Dict[str, Any]:
        """Reject proposed action without applying restrictions."""
        incident = incident_store.get(incident_id)
        if not incident:
            return {"status": "error", "message": f"Incident '{incident_id}' not found"}

        incident_store.update_status(incident_id, "rejected", actor=actor)
        action_policy.log_action("reject", incident.sender, "rejected_by_human", {"incident_id": incident_id})

        return {
            "status": "success",
            "incident_id": incident_id,
            "action": "rejected",
            "message": "Proposed defense action rejected by operator"
        }

    def undo_action(self, incident_id: str) -> Dict[str, Any]:
        """Undo a previously executed defense action (reversibility guarantee)."""
        matching = [r for r in self.execution_history if r["incident_id"] == incident_id and not r["undone"]]
        if not matching:
            return {"status": "error", "message": "No active reversible action found"}

        record = matching[-1]
        action = record["action"]
        target = record["target"]

        if action == "quarantine":
            self.quarantined_items = [q for q in self.quarantined_items if q["incident_id"] != incident_id]
        elif action == "block_sender":
            self.blocked_senders.discard(target.lower())
        elif action == "block_url":
            self.blocked_urls.discard(target.lower())

        record["undone"] = True
        incident_store.update_status(incident_id, "pending_approval", actor="undo_operator")

        return {
            "status": "success",
            "incident_id": incident_id,
            "undone_action": action,
            "message": f"Action '{action}' successfully reversed"
        }

executor = ActionExecutor()
