"""Layer 3: Output Guardrail.
Validates Verdict structure, grounds evidence against tools that actually executed,
enforces label-score consistency, caps unsupported claims, and defangs all URLs.
"""
from typing import List, Set, Dict, Any
from scamshield_agent.schemas import Verdict, Evidence
from .defang import defang

SCORE_LABEL_THRESHOLDS = {
    "safe": (0, 35),
    "suspicious": (30, 65),
    "likely_scam": (60, 85),
    "scam": (75, 100)
}

def validate_verdict(v: Verdict, executed_tools: Set[str]) -> Verdict:
    """Validate and filter verdict against grounded tools and safety policies."""
    # 1. Grounding check: drop evidence from tools that never ran
    v.evidence = [e for e in v.evidence if e.source_tool in executed_tools]
    
    # 2. Evidence count requirement: fewer than 2 independent sources caps label at suspicious
    independent_tools = {e.source_tool for e in v.evidence}
    if len(independent_tools) < 2 and v.label in ("likely_scam", "scam"):
        v.label = "suspicious"
        if v.risk_score > 60:
            v.risk_score = 60
            
    # 3. Score-label consistency
    if v.risk_score >= 80 and v.label == "safe":
        v.label = "suspicious"
    elif v.risk_score <= 20 and v.label in ("likely_scam", "scam"):
        v.label = "safe"

    # 4. Defang explanations
    v.explanation_en = defang(v.explanation_en)
    v.explanation_local = defang(v.explanation_local)
    
    return v
