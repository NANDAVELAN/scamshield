"""Deterministic rules-based reflex scorer and offline verdict generator."""
import time
import re
from typing import Dict, Any, List
from scamshield_agent.schemas import TriageResult, Verdict, Evidence
from scamshield_agent.tools.url_tools import check_lookalike, get_domain_age, check_blocklist
from scamshield_agent.tools.sender_tools import get_sender_reputation, check_email_auth
from scamshield_agent.tools.attachment_tools import analyze_attachment
from scamshield_agent.tools.entities import extract_entities
from guardrails.defang import defang

SCAM_PATTERNS = {
    "fake_kyc": [
        r'\bkyc\b', r'\baadhaar\b', r'\bpan card\b', r'\baccount (suspended|blocked|deactivated)\b',
        r'\bupdate kyc\b', r'\bnet ?banking services are temporarily blocked\b'
    ],
    "upi_refund": [
        r'\brefund\b', r'\bcashback\b', r'\bwallet\b', r'\bclaim.*money\b', r'\bupi refund\b'
    ],
    "courier": [
        r'\bparcel\b', r'\bpackage\b', r'\bcustoms\b', r'\bdelivery fee\b',
        r'\bwrong address\b', r'\bindia post\b'
    ],
    "bill_disconnect": [
        r'\belectricity\b', r'\bpower (will be )?disconnected\b', r'\bbill was not updated\b',
        r'\bbescom\b', r'\bpower cut\b'
    ],
    "job_offer": [
        r'\bpart[- ]time\b', r'\bearn \d+.*daily\b', r'\bliking youtube\b',
        r'\brating products\b', r'\btelegram @'
    ],
    "digital_arrest": [
        r'\bdigital arrest\b', r'\barrest warrant\b', r'\bnarcotics\b',
        r'\bcbi\b', r'\bmumbai police\b', r'\bvideo interrogation\b'
    ],
    "lottery": [
        r'\blottery\b', r'\blucky draw\b', r'\bcrorepati\b', r'\b25 lakh\b', r'\bwinner\b'
    ],
    "otp_request": [
        r'\bshare (the )?otp\b', r'\bcancellation otp\b', r'\brepresentative to block\b'
    ]
}

URGENCY_KEYWORDS = [
    r'\bimmediately\b', r'\burgent\b', r'\bwithin 24 hours\b', r'\btonight at\b',
    r'\bexpires today\b', r'\bfinal demand\b', r'\bnon-bailable\b', r'\bpenalty\b'
]

def score_rules(message: Dict[str, Any]) -> TriageResult:
    """Fast reflex scoring based on deterministic rules, heuristics, and mock intelligence.
    
    Returns:
        TriageResult: Fast calibrated triage scoring.
    """
    start_time = time.perf_counter()

    sender = message.get("sender", "")
    subject = message.get("subject", "")
    body = message.get("body", "")
    urls = message.get("urls", [])
    attachments = message.get("attachments", [])
    headers = message.get("headers", {})

    full_text = f"{subject} {body}".strip()
    full_text_lower = full_text.lower()

    # 1. Entity extraction
    extracted = extract_entities(full_text)
    all_domains = list(set(extracted.get("domains", [])))
    all_urls = list(set(urls + extracted.get("urls", [])))

    # 2. Check Urgency
    urgency_hits = 0
    for kw in URGENCY_KEYWORDS:
        if re.search(kw, full_text_lower):
            urgency_hits += 2
    urgency = min(10, urgency_hits)

    # 3. Detect Scam Type
    detected_type = "none"
    max_type_hits = 0
    for stype, patterns in SCAM_PATTERNS.items():
        hits = sum(1 for p in patterns if re.search(p, full_text_lower))
        if hits > max_type_hits:
            max_type_hits = hits
            detected_type = stype

    # 4. Reputation & Auth Evaluation
    sender_rep = get_sender_reputation(sender)
    auth_check = check_email_auth(headers)

    # Risk Accumulator (0 to 100)
    risk_score = 0
    brand_impersonation = 0.0

    # Sender indicators
    if sender_rep.get("is_malicious", False):
        risk_score += 40
    if sender_rep.get("reports", 0) > 20:
        risk_score += 20
    if auth_check.get("is_spoofed", False):
        risk_score += 30

    # URL & Domain indicators
    for d in all_domains:
        lookalike = check_lookalike(d)
        if lookalike.get("is_lookalike", False):
            risk_score += 40
            brand_impersonation = 0.95
        age = get_domain_age(d)
        if age.get("is_new", False):
            risk_score += 35
        if age.get("reports", 0) > 20:
            risk_score += 25
        bl = check_blocklist(d)
        if bl.get("is_blocked", False):
            risk_score += 50

    # Sender blocklist check
    if sender:
        bl_sender = check_blocklist(sender)
        if bl_sender.get("is_blocked", False):
            risk_score += 50

    # Attachment indicators
    for att in attachments:
        name = att.get("name", "") if isinstance(att, dict) else str(att)
        att_analysis = analyze_attachment(name)
        if att_analysis.get("is_suspicious", False):
            risk_score += 45

    # Urgency & Pattern Boost
    if max_type_hits >= 2:
        risk_score += 30
    elif max_type_hits == 1:
        risk_score += 15

    if urgency >= 6:
        risk_score += 15

    # Mitigating factors for legitimate messages
    if auth_check.get("auth_passed", False):
        # Officially authenticated sender
        if not all_domains or all(check_lookalike(d).get("is_official", False) for d in all_domains):
            risk_score = max(0, risk_score - 60)

    # If sender is verified and 0 reports
    if "verified" in sender_rep.get("tag", "") and sender_rep.get("reports", 0) == 0:
        risk_score = max(0, risk_score - 40)

    # Normalize probability
    prob = min(1.0, max(0.0, risk_score / 100.0))
    if detected_type != "none" and prob < 0.3 and (urgency > 4 or max_type_hits >= 1):
        prob = 0.4

    latency_ms = max(1, int((time.perf_counter() - start_time) * 1000))

    return TriageResult(
        scam_probability=round(prob, 2),
        scam_type=detected_type if prob >= 0.3 else "none",
        urgency=urgency,
        impersonates_brand=brand_impersonation,
        source="rules",
        latency_ms=latency_ms
    )

def rules_only_verdict(message: Dict[str, Any]) -> Verdict:
    """Generate a comprehensive Verdict strictly from deterministic rules and mock datasets.
    
    Used as the ultimate fallback in the LLM router when all cloud and local models are unavailable.
    """
    triage = score_rules(message)
    sender = message.get("sender", "")
    urls = message.get("urls", [])
    attachments = message.get("attachments", [])
    headers = message.get("headers", {})

    evidence: List[Evidence] = []
    risk_score = int(triage.scam_probability * 100)

    # Gather concrete evidence
    for u in urls:
        extracted = extract_entities(u)
        for d in extracted.get("domains", []):
            lk = check_lookalike(d)
            if lk.get("is_lookalike"):
                evidence.append(Evidence(
                    source_tool="check_lookalike",
                    finding=f"Domain '{d}' impersonates brand '{lk.get('target_brand')}'",
                    weight=0.9
                ))
            age = get_domain_age(d)
            if age.get("is_new"):
                evidence.append(Evidence(
                    source_tool="get_domain_age",
                    finding=f"Domain registered only {age.get('age_days')} days ago with {age.get('reports')} fraud reports",
                    weight=0.85
                ))

    # Sender evidence
    s_rep = get_sender_reputation(sender)
    if s_rep.get("is_malicious"):
        evidence.append(Evidence(
            source_tool="get_sender_reputation",
            finding=f"Sender flagged with {s_rep.get('reports')} community reports ({s_rep.get('tag')})",
            weight=0.8
        ))

    # Auth evidence
    auth = check_email_auth(headers)
    if auth.get("is_spoofed"):
        evidence.append(Evidence(
            source_tool="check_email_auth",
            finding=f"Email authentication failed: SPF={auth.get('spf')}, DKIM={auth.get('dkim')}",
            weight=0.75
        ))

    # Attachment evidence
    for att in attachments:
        name = att.get("name", "") if isinstance(att, dict) else str(att)
        att_eval = analyze_attachment(name)
        if att_eval.get("is_suspicious"):
            evidence.append(Evidence(
                source_tool="analyze_attachment",
                finding=f"Malicious attachment detected: {', '.join(att_eval.get('reasons', []))}",
                weight=0.95
            ))

    # Label assignment
    if risk_score >= 75:
        label = "scam"
        rec_action = "quarantine"
    elif risk_score >= 50:
        label = "likely_scam"
        rec_action = "quarantine"
    elif risk_score >= 30:
        label = "suspicious"
        rec_action = "warn"
    else:
        label = "safe"
        rec_action = "none"

    # Human-readable explanations
    if label in ("scam", "likely_scam"):
        en_exp = f"Scam detected ({triage.scam_type}): The message exhibits suspicious urgency, unauthorized domains, or spoofed origin."
        ta_exp = f"மோசடி எச்சரிக்கை ({triage.scam_type}): இந்த செய்தி அங்கீகரிக்கப்படாத இணைப்பு அல்லது போலி மூலத்தை கொண்டுள்ளது."
    elif label == "suspicious":
        en_exp = f"Suspicious communication ({triage.scam_type}): Review sender details before interacting."
        ta_exp = "சந்தேகத்திற்குரிய செய்தி: இணைப்புகளை திறக்கும் முன் அனுப்புநரை சரிபார்க்கவும்."
    else:
        en_exp = "No known scam indicators detected. The sender and content appear legitimate."
        ta_exp = "பாதுகாப்பான செய்தி: எந்த மோசடி அறிகுறிகளும் கண்டறியப்படவில்லை."

    return Verdict(
        risk_score=risk_score,
        label=label,
        scam_type=triage.scam_type,
        evidence=evidence,
        explanation_en=defang(en_exp),
        explanation_local=defang(ta_exp),
        recommended_action=rec_action
    )
