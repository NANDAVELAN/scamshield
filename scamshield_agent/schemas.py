from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List, Dict, Any, Union

class Evidence(BaseModel):
    source_tool: str                      # e.g. "get_domain_age"
    finding: str
    weight: float = Field(default=0.5, ge=0, le=1)

class TriageResult(BaseModel):
    scam_probability: float = Field(ge=0, le=1)
    scam_type: str
    urgency: int = Field(ge=0, le=10)
    impersonates_brand: float = Field(ge=0, le=1)
    source: Literal["jev", "gemini_flash", "rules"]
    latency_ms: int
    status: Optional[str] = Field(default="escalated")
    reason: Optional[str] = Field(default=None)

class Verdict(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    label: Literal["safe", "suspicious", "likely_scam", "scam"]
    scam_type: str
    evidence: list[Evidence] = Field(default_factory=list)
    explanation_en: str
    explanation_local: str
    recommended_action: Literal["none", "warn", "quarantine", "block_sender", "block_url"]

class AttachmentInfo(BaseModel):
    name: str
    size_kb: Optional[float] = 0.0

class AnalyzeRequest(BaseModel):
    channel: str = "gmail"
    sender: str
    subject: Optional[str] = ""
    body: str
    urls: list[str] = Field(default_factory=list)
    attachments: list[AttachmentInfo] = Field(default_factory=list)
    headers: dict[str, str] = Field(default_factory=dict)
    language_pref: str = "en"

    @field_validator("attachments", mode="before")
    @classmethod
    def normalize_attachments(cls, v):
        if not v:
            return []
        res = []
        for item in v:
            if isinstance(item, str):
                res.append({"name": item, "size_kb": 0.0})
            elif isinstance(item, dict):
                res.append(item)
            else:
                res.append(item)
        return res

class AnalyzeResponse(BaseModel):
    incident_id: str
    triage: Optional[TriageResult] = None
    verdict: Verdict
    provider_used: str
    cache_hit: bool = False
    status: Literal["pending_approval", "approved", "rejected", "auto_executed"] = "pending_approval"
    campaign_id: Optional[str] = None

class Incident(BaseModel):
    incident_id: str
    created_at: float
    channel: str
    sender: str
    subject: Optional[str] = ""
    body: str
    urls: list[str] = Field(default_factory=list)
    attachments: list[AttachmentInfo] = Field(default_factory=list)
    triage: Optional[TriageResult] = None
    verdict: Optional[Verdict] = None
    proposed_action: str = "none"
    status: Literal["pending_approval", "approved", "rejected", "auto_executed"] = "pending_approval"
    provider_used: str = "rules"
    cache_hit: bool = False
    campaign_id: Optional[str] = None
    audit_log: list[dict] = Field(default_factory=list)

    @field_validator("attachments", mode="before")
    @classmethod
    def normalize_attachments(cls, v):
        if not v:
            return []
        res = []
        for item in v:
            if isinstance(item, str):
                res.append({"name": item, "size_kb": 0.0})
            elif isinstance(item, dict):
                res.append(item)
            else:
                res.append(item)
        return res
