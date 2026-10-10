"""FastAPI application for ScamShield backend with /analyze, /health, and /stream SSE endpoints."""
import os
import time
import json
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from .schemas import Message, Verdict, Evidence
from .rules_engine import analyze_rules

app = FastAPI(
    title="ScamShield API",
    description="Anti-scam notification defense agent API",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Streaming subscriber queues for /stream
sse_subscribers: List[asyncio.Queue] = []

def get_current_time_str() -> str:
    return time.strftime("%H:%M:%S")

async def broadcast_pipeline_log(agent: str, message_text: str, stage: int = 0):
    """Broadcasts a live log line to SSE subscribers formatted as: [HH:MM:SS] Agent: message."""
    t_str = get_current_time_str()
    log_line = f"[{t_str}] {agent}: {message_text}"
    event_payload = json.dumps({
        "timestamp": t_str,
        "agent": agent,
        "message": message_text,
        "stage": stage,
        "log_line": log_line
    })
    msg = f"data: {event_payload}\n\n"
    for q in list(sse_subscribers):
        try:
            q.put_nowait(msg)
        except Exception:
            pass

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    mode = os.getenv("MODE", "rules").lower()
    return {
        "status": "ok",
        "service": "ScamShield",
        "mode": mode,
        "timestamp": time.time(),
        "active_stream_clients": len(sse_subscribers)
    }

@app.get("/stream")
async def pipeline_stream(request: Request):
    """Server-Sent Events endpoint emitting live pipeline logs."""
    queue = asyncio.Queue()
    sse_subscribers.append(queue)

    async def event_generator():
        try:
            # Initial connection greeting
            t_str = get_current_time_str()
            initial = json.dumps({
                "timestamp": t_str,
                "agent": "System",
                "message": "Connected to ScamShield live stream",
                "stage": 0,
                "log_line": f"[{t_str}] System: Connected to ScamShield live stream"
            })
            yield f"data: {initial}\n\n"
            
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

@app.post("/analyze", response_model=Verdict)
async def analyze_endpoint(message: Message):
    """Analyzes an incoming message and broadcasts each step to the /stream endpoint."""
    t_start = time.perf_counter()
    mode = os.getenv("MODE", "rules").lower()
    
    # Broadcast pipeline steps
    await broadcast_pipeline_log("Triage", f"Incoming {message.channel} alert from {message.sender}", stage=0)
    
    # 1. Reflex stage
    from .reflex import default_reflex_gate
    r_score, r_lat = default_reflex_gate.evaluate(message)
    await broadcast_pipeline_log("Reflex", f"Reflex gate returned in {int(r_lat)}ms with score {r_score:.2f}", stage=0)

    # 2. Router / Execution
    # If MODE is llm or auto, we will route to ADK agent in Phase 3; in rules mode (or fallback), we execute rules_engine.
    if mode in ("llm", "auto"):
        try:
            from .router import analyze_with_agent_router
            verdict = await analyze_with_agent_router(message, broadcast_callback=broadcast_pipeline_log)
        except Exception as e:
            await broadcast_pipeline_log("Router", f"LLM error: {e}. Executing safe rules fallback.", stage=4)
            verdict = analyze_rules(message)
    else:
        # Rules mode
        await broadcast_pipeline_log("URL", f"URL Investigator: {message.urls or 'Checking links'}", stage=1)
        await broadcast_pipeline_log("Sender", f"Sender Investigator: Checking {message.sender}", stage=2)
        await broadcast_pipeline_log("Attachment", f"Attachment Investigator: {len(message.attachments)} files", stage=3)
        await broadcast_pipeline_log("Synthesizer", "Synthesizing verdict using rules...", stage=4)
        verdict = analyze_rules(message)

    latency_ms = max(1.0, (time.perf_counter() - t_start) * 1000)
    verdict.latency_ms = latency_ms

    await broadcast_pipeline_log("Verdict", f"Finalized: {verdict.verdict} ({verdict.score}/100). Recommended: {verdict.action}", stage=4)
    return verdict

# Static UI serving for browser preview / mobile assets
static_ui_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scamshield-mobile.html")
@app.get("/")
async def root_ui():
    if os.path.exists(static_ui_path):
        return FileResponse(static_ui_path)
    return {"message": "ScamShield backend running"}
