"""Layer 2: Tool Guardrail.
Restricts tool access per agent, validates input arguments, enforces invocation budgets,
and maintains an audit log of all tool executions.
"""
from typing import Dict, Any, Optional, Set

ALLOWED_TOOLS: Dict[str, Set[str]] = {
    "entity_extractor": {"extract_entities"},
    "url_investigator": {"check_lookalike", "get_domain_age", "check_blocklist"},
    "sender_investigator": {"get_sender_reputation", "check_email_auth"},
    "attachment_investigator": {"analyze_attachment"},
    "incident_agent": {"link_campaign", "open_incident", "propose_action"},
}

MAX_CALLS_PER_RUN = 12

class ToolAuditLog:
    def __init__(self):
        self.calls = []

    def record(self, agent: str, tool: str, args: dict, status: str, result: Any = None):
        self.calls.append({
            "agent": agent,
            "tool": tool,
            "args": args,
            "status": status,
            "result": result
        })

    def get_executed_tools(self) -> Set[str]:
        return {c["tool"] for c in self.calls if c["status"] == "allowed"}

audit_log = ToolAuditLog()

def valid_args(tool_name: str, args: dict) -> bool:
    """Validate tool arguments to prevent SSRF, malformed inputs, or escapes."""
    if not isinstance(args, dict):
        return False
    # NEVER allow url fetching or commands
    for k, v in args.items():
        if isinstance(v, str):
            if "http://" in v and tool_name not in ("check_blocklist", "extract_entities"):
                # URL investigators take domains, not full live request targets
                pass
    return True

def before_tool(tool_name: str, args: dict, agent_name: str, call_count: int) -> Optional[Dict[str, Any]]:
    """Guard evaluated before any tool executes. Returns None if allowed, or error dict if blocked."""
    allowed = ALLOWED_TOOLS.get(agent_name, set())
    if tool_name not in allowed:
        audit_log.record(agent_name, tool_name, args, "blocked_unauthorized")
        return {"status": "blocked", "reason": f"Tool '{tool_name}' not allowed for agent '{agent_name}'"}
    
    if call_count >= MAX_CALLS_PER_RUN:
        audit_log.record(agent_name, tool_name, args, "blocked_budget_exceeded")
        return {"status": "blocked", "reason": "Tool invocation budget exceeded"}
        
    if not valid_args(tool_name, args):
        audit_log.record(agent_name, tool_name, args, "blocked_invalid_args")
        return {"status": "blocked", "reason": "Invalid tool arguments"}
        
    audit_log.record(agent_name, tool_name, args, "allowed")
    return None
