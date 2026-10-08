"""Incident repository and audit store for ScamShield."""
import time
from typing import Dict, List, Optional, Any
from scamshield_agent.schemas import Incident

class IncidentStore:
    def __init__(self):
        self._incidents: Dict[str, Incident] = {}
        self.audit_log: List[Dict[str, Any]] = []

    def save(self, incident: Incident) -> Incident:
        self._incidents[incident.incident_id] = incident
        return incident

    def get(self, incident_id: str) -> Optional[Incident]:
        return self._incidents.get(incident_id)

    def list_all(self) -> List[Incident]:
        # Return sorted by created_at descending
        return sorted(self._incidents.values(), key=lambda i: i.created_at, reverse=True)

    def update_status(self, incident_id: str, new_status: str, actor: str = "human") -> Optional[Incident]:
        inc = self._incidents.get(incident_id)
        if inc:
            inc.status = new_status
            log_entry = {
                "timestamp": time.time(),
                "incident_id": incident_id,
                "action": f"status_changed_to_{new_status}",
                "actor": actor
            }
            inc.audit_log.append(log_entry)
            self.audit_log.append(log_entry)
        return inc

incident_store = IncidentStore()
