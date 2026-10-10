"""Control Center API endpoints for ScamShield."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from llm.router import router
from guardrails.action_policy import action_policy
from server.cache import verdict_cache
from server.store import incident_store

router_control = APIRouter(prefix="/control", tags=["Control"])

# Runtime config state
CONTROL_STATE = {
    "flag_threshold": 0.80,
    "ignore_threshold": 0.30,
    "paused": False
}

class ProviderUpdateRequest(BaseModel):
    force: Optional[str] = None
    simulate_outage: Optional[List[str]] = None

class ModeUpdateRequest(BaseModel):
    autonomy: Optional[str] = Field(default=None, pattern="^(observe|ask|auto_low_risk)$")
    privacy: Optional[bool] = None
    paused: Optional[bool] = None

class ThresholdUpdateRequest(BaseModel):
    flag: float = Field(ge=0.0, le=1.0)
    ignore: float = Field(ge=0.0, le=1.0)

@router_control.get("/state")
def get_control_state():
    """Retrieve full operator state for Mission Control panel."""
    router_status = router.get_status()
    return {
        "status": "active" if not CONTROL_STATE["paused"] else "paused",
        "paused": CONTROL_STATE["paused"],
        "thresholds": {
            "flag": CONTROL_STATE["flag_threshold"],
            "ignore": CONTROL_STATE["ignore_threshold"]
        },
        "autonomy_mode": action_policy.autonomy_mode,
        "auto_actions_today": action_policy.auto_actions_today,
        "providers": router_status["providers"],
        "forced_provider": router_status["forced"],
        "privacy_mode": router_status["privacy_mode"],
        "cache": router_status["cache_stats"],
        "total_incidents": len(incident_store.list_all())
    }

@router_control.post("/provider")
def update_provider_settings(req: ProviderUpdateRequest):
    """Force a specific provider or simulate outage for testing/demo."""
    if req.force is not None:
        router.forced = req.force if req.force != "" else None
    if req.simulate_outage is not None:
        router.simulate_outage = set(req.simulate_outage)
    return {"status": "success", "state": router.get_status()}

@router_control.post("/mode")
def update_mode_settings(req: ModeUpdateRequest):
    """Update autonomy dial, privacy mode, or pause switch."""
    if req.autonomy:
        action_policy.autonomy_mode = req.autonomy
    if req.privacy is not None:
        router.privacy_mode = req.privacy
    if req.paused is not None:
        CONTROL_STATE["paused"] = req.paused
    return {"status": "success", "mode": {
        "autonomy": action_policy.autonomy_mode,
        "privacy": router.privacy_mode,
        "paused": CONTROL_STATE["paused"]
    }}

@router_control.post("/thresholds")
def update_thresholds(req: ThresholdUpdateRequest):
    """Update quick triage gating thresholds."""
    CONTROL_STATE["flag_threshold"] = req.flag
    CONTROL_STATE["ignore_threshold"] = req.ignore
    return {"status": "success", "thresholds": CONTROL_STATE}

@router_control.post("/clear-cache")
def clear_verdict_cache():
    """Clear message-hash cache for demo repeatability."""
    verdict_cache.clear()
    return {"status": "success", "message": "Cache successfully cleared"}

@router_control.get("/audit")
def get_audit_trail():
    """Return append-only audit trail."""
    return {"audit_log": action_policy.audit_log}

@router_control.get("/harness")
def get_harness_report():
    """Get latest safety harness report and invariant statuses."""
    import os
    import json
    report_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "harness", "harness_report.json")
    if os.path.exists(report_path):
        with open(report_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Generate on the fly if missing
    from harness.run import run_golden_suite, run_adversarial_suite, verify_all_invariants
    import time
    golden = run_golden_suite()
    adv = run_adversarial_suite()
    invariants, all_passed = verify_all_invariants()
    return {
        "timestamp": time.time(),
        "metrics": golden,
        "adversarial": adv,
        "invariants": invariants,
        "all_invariants_passed": all_passed
    }

@router_control.post("/harness/run")
def trigger_harness_run():
    """Trigger live execution of safety harness and invariant assertions."""
    import time
    from harness.run import run_golden_suite, run_adversarial_suite, verify_all_invariants
    from harness.report import generate_report
    
    golden = run_golden_suite()
    adv = run_adversarial_suite()
    invariants, all_passed = verify_all_invariants()
    
    report_payload = {
        "timestamp": time.time(),
        "metrics": golden,
        "adversarial": adv,
        "invariants": invariants,
        "all_invariants_passed": all_passed
    }
    generate_report(report_payload)
    return {"status": "success", "report": report_payload}
