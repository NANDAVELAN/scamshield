"""FastAPI application for ScamShield cognitive defense backend and SSE streaming."""
# Reload trigger 2
import asyncio
import json
import os
import time
import uuid
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from scamshield_agent.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    Incident,
    Verdict,
    TriageResult
)
from scamshield_agent.tools.campaign_tools import link_campaign
import importlib
import scamshield_agent.tools.url_tools
import scamshield_agent.tools.sender_tools
import triage.rules
import triage.jev_client
import llm.router
importlib.reload(scamshield_agent.tools.url_tools)
importlib.reload(scamshield_agent.tools.sender_tools)
importlib.reload(triage.rules)
importlib.reload(triage.jev_client)
importlib.reload(llm.router)

from triage.rules import score_rules
from triage.jev_client import quick_triage
from llm.router import router, analyze_with_router
from .store import incident_store
from .executor import executor
from .control import router_control, CONTROL_STATE


app = FastAPI(
    title="ScamShield API",
    description="Agentic Scam Protection API with reflex triage and explainable multi-agent investigation",
    version="1.0.0"
)

# CORS setup
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080,chrome-extension://*")
origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Control endpoints
app.include_router(router_control)

# SSE Event Broadcasting Channel
sse_subscribers: List[asyncio.Queue] = []

async def broadcast_sse_event(stage: str, agent: str, status: str, provider: str, latency_ms: int, payload: dict = None):
    """Broadcast structured pipeline events to all connected SSE clients."""
    event_data = {
        "stage": stage,
        "agent": agent,
        "status": status,
        "provider": provider,
        "latency_ms": latency_ms,
        "payload": payload or {}
    }
    msg = f"data: {json.dumps(event_data)}\n\n"
    for queue in list(sse_subscribers):
        try:
            queue.put_nowait(msg)
        except Exception:
            pass

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "env": os.getenv("SCAMSHIELD_ENV", "local"),
        "timestamp": time.time(),
        "active_sse_clients": len(sse_subscribers)
    }

@app.get("/analyze/stream")
async def analyze_stream(request: Request):
    """Server-Sent Events endpoint streaming live agent pipeline execution."""
    queue = asyncio.Queue()
    sse_subscribers.append(queue)

    async def event_generator():
        try:
            # Send initial keepalive
            yield f"data: {json.dumps({'stage': 'connect', 'status': 'connected', 'timestamp': time.time()})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield data
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            if queue in sse_subscribers:
                sse_subscribers.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_message(req: AnalyzeRequest):
    """Analyze incoming message through reflex triage, model router, and agent investigation."""
    if CONTROL_STATE["paused"]:
        raise HTTPException(status_code=503, detail="ScamShield analysis is currently paused by operator")

    req_dict = req.model_dump()
    start_total = time.perf_counter()

    # 1. Reflex triage (System One: Jev -> Flash JSON -> Rules)
    await broadcast_sse_event("triage", "reflex_gate", "start", "active_reflex", 0)
    t_start = time.perf_counter()
    triage_res = await quick_triage(req_dict)
    t_latency = int((time.perf_counter() - t_start) * 1000)
    await broadcast_sse_event(
        "triage", "reflex_gate", "done", triage_res.source, t_latency,
        {"probability": triage_res.scam_probability, "scam_type": triage_res.scam_type}
    )

    # 2. Reflex gate decision
    # If probability < ignore threshold and no urgent threats, skip heavy investigation
    if triage_res.scam_probability < CONTROL_STATE["ignore_threshold"] and triage_res.urgency <= 2:
        verdict = Verdict(
            risk_score=int(triage_res.scam_probability * 100),
            label="safe",
            scam_type="none",
            evidence=[],
            explanation_en="Reflex evaluation detected no threats or suspicious indicators.",
            explanation_local="எந்த மோசடி அறிகுறிகளும் கண்டறியப்படவில்லை.",
            recommended_action="none"
        )
        provider_used = "rules"
        cache_hit = False
    else:
        # 3. Deep Investigation via LLM Router (System Two)
        await broadcast_sse_event("investigator", "url_investigator", "start", "active_provider", 0)
        await broadcast_sse_event("investigator", "sender_investigator", "start", "active_provider", 0)
        await broadcast_sse_event("investigator", "attachment_investigator", "start", "active_provider", 0)

        inv_start = time.perf_counter()
        provider_used, verdict, cache_hit = await analyze_with_router(router, req_dict)
        inv_latency = int((time.perf_counter() - inv_start) * 1000)

        await broadcast_sse_event("verdict", "verdict_agent", "done", provider_used, inv_latency, {
            "risk_score": verdict.risk_score,
            "label": verdict.label
        })

    # 4. Campaign clustering
    camp_res = link_campaign(req.sender, req.urls[0] if req.urls else "")
    campaign_id = camp_res.get("campaign_id")

    # 5. Open Incident record
    incident_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
    status = "pending_approval"
    proposed_act = verdict.recommended_action

    # Check Autonomy policy for potential auto-action
    if executor:
        from guardrails.action_policy import action_policy
        can_auto, _ = action_policy.can_execute(
            action=proposed_act,
            target=req.sender,
            risk_score=verdict.risk_score,
            evidence_count=len(verdict.evidence),
            approved=False
        )
        if can_auto and action_policy.autonomy_mode == "auto_low_risk":
            executor.execute_incident_action(incident_id, approved=False, actor="autonomy_agent")
            status = "auto_executed"

    incident = Incident(
        incident_id=incident_id,
        created_at=time.time(),
        channel=req.channel,
        sender=req.sender,
        subject=req.subject,
        body=req.body,
        urls=req.urls,
        attachments=req.attachments,
        triage=triage_res,
        verdict=verdict,
        proposed_action=proposed_act,
        status=status,
        provider_used=provider_used,
        cache_hit=cache_hit,
        campaign_id=campaign_id
    )
    incident_store.save(incident)

    await broadcast_sse_event("incident", "incident_agent", "done", provider_used, 10, {
        "incident_id": incident_id,
        "proposed_action": proposed_act,
        "status": status
    })

    return AnalyzeResponse(
        incident_id=incident_id,
        triage=triage_res,
        verdict=verdict,
        provider_used=provider_used,
        cache_hit=cache_hit,
        status=status,
        campaign_id=campaign_id
    )

@app.get("/incidents", response_model=List[Incident])
async def list_incidents():
    """Retrieve all open and historical incidents."""
    return incident_store.list_all()

@app.get("/incidents/{incident_id}", response_model=Incident)
async def get_incident(incident_id: str):
    """Retrieve details for a specific incident."""
    inc = incident_store.get(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return inc

@app.post("/incidents/{incident_id}/approve")
async def approve_incident(incident_id: str):
    """Approve proposed defense action (quarantine or block) via safe executor."""
    res = executor.execute_incident_action(incident_id, approved=True, actor="human_operator")
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res.get("message"))
    return res

@app.post("/incidents/{incident_id}/reject")
async def reject_incident(incident_id: str):
    """Reject proposed defense action."""
    res = executor.reject_incident_action(incident_id, actor="human_operator")
    if res.get("status") == "error":
        raise HTTPException(status_code=404, detail=res.get("message"))
    return res

@app.post("/incidents/{incident_id}/undo")
async def undo_incident_action(incident_id: str):
    """Undo previously executed action (reversibility guarantee)."""
    res = executor.undo_action(incident_id)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

from fastapi.responses import RedirectResponse

@app.get("/")
async def root_redirect():
    return RedirectResponse(url="/control/ui")

@app.get("/control")
async def control_redirect():
    return RedirectResponse(url="/control/ui")

# Static files for Control Center UI
control_ui_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "control_center")
if os.path.exists(control_ui_dir):
    app.mount("/control/ui", StaticFiles(directory=control_ui_dir, html=True), name="control_ui")

# Static files for Simulator
simulator_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "simulator")
if os.path.exists(simulator_dir):
    app.mount("/simulator", StaticFiles(directory=simulator_dir, html=True), name="simulator")
