"""Pydantic schemas for ScamShield common message and verdict formats."""
from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field

class Attachment(BaseModel):
    name: str
    mime: Optional[str] = "application/octet-stream"

class Message(BaseModel):
    id: Optional[Union[str, int]] = None
    channel: Literal["whatsapp", "sms", "gmail", "web"] = "web"
    sender: str
    body: str
    urls: List[str] = Field(default_factory=list)
    attachments: List[Attachment] = Field(default_factory=list)
    headers: Dict[str, str] = Field(default_factory=dict)
    timestamp: Optional[Union[float, int, str]] = None

class Evidence(BaseModel):
    reflex: Optional[str] = None
    url: Optional[str] = None
    sender: Optional[str] = None
    attachment: Optional[str] = None

class Verdict(BaseModel):
    verdict: Literal["safe", "suspicious", "scam"]
    score: int = Field(ge=0, le=100)
    action: Literal["allow", "warn", "block"]
    reason: str
    evidence: Evidence
    mode: Literal["rules", "llm"] = "rules"
    latency_ms: float = 0.0

class PipelineLog(BaseModel):
    timestamp: str
    agent: str
    message: str
    stage: int
