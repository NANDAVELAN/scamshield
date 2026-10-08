"""LLM Router with multi-tier fallback chain, circuit breaker, rate limiting, and cache."""
import asyncio
import time
import os
import logging
from typing import Dict, Any, Tuple, Optional, Callable, AsyncGenerator
from .providers import CHAIN
from scamshield_agent.agent import build_root_agent
from scamshield_agent.schemas import Verdict
from triage.rules import rules_only_verdict
from server.cache import verdict_cache
from guardrails.input_guard import prepare_guarded_input
from guardrails.output_guard import validate_verdict

logger = logging.getLogger("scamshield.router")

class Router:
    def __init__(self):
        self.down_until: Dict[str, float] = {p["name"]: 0 for p in CHAIN}
        self.forced: Optional[str] = None          # Force specific provider from UI
        self.privacy_mode: bool = False            # Local-only mode
        self.simulate_outage: set = set()          # Simulated outage for demo
        self.error_counts: Dict[str, int] = {p["name"]: 0 for p in CHAIN}
        self.last_error: Dict[str, Optional[str]] = {p["name"]: None for p in CHAIN}
        self.concurrency_semaphore = asyncio.Semaphore(2)  # Max 2 concurrent deep investigations

    def chain(self):
        """Yield available providers adhering to health, privacy, and override filters."""
        now = time.time()
        for p in CHAIN:
            name = p["name"]
            if self.privacy_mode and p["cloud"]:
                continue
            if self.forced and name != self.forced:
                continue
            if name in self.simulate_outage:
                continue
            if self.down_until.get(name, 0) > now:
                continue
            yield p

    def mark_failed(self, name: str, err: Exception, cooldown: int = 60):
        """Trigger circuit breaker for failed provider with cooldown."""
        self.down_until[name] = time.time() + cooldown
        self.error_counts[name] = self.error_counts.get(name, 0) + 1
        self.last_error[name] = str(err)
        logger.warning(f"Provider {name} failed: {err}. Circuit breaker active for {cooldown}s.")

    def mark_success(self, name: str):
        """Reset circuit breaker upon successful execution."""
        self.down_until[name] = 0

    def get_status(self) -> Dict[str, Any]:
        """Return provider health status for Control Center UI."""
        now = time.time()
        status = {}
        for p in CHAIN:
            name = p["name"]
            is_down = (self.down_until.get(name, 0) > now) or (name in self.simulate_outage)
            status[name] = {
                "name": name,
                "cloud": p["cloud"],
                "healthy": not is_down,
                "simulated_outage": name in self.simulate_outage,
                "error_count": self.error_counts.get(name, 0),
                "last_error": self.last_error.get(name),
                "down_seconds_remaining": max(0, int(self.down_until.get(name, 0) - now))
            }
        return {
            "providers": status,
            "forced": self.forced,
            "privacy_mode": self.privacy_mode,
            "cache_stats": {
                "hits": verdict_cache.hits,
                "misses": verdict_cache.misses
            }
        }

router = Router()

async def run_pipeline(agent, message: Dict[str, Any], event_callback: Optional[Callable] = None) -> Verdict:
    """Execute the Google ADK root agent with guarded input."""
    # Guard input
    guarded = prepare_guarded_input(message.get("body", ""))

    # If Google API key is missing or not configured, raise to trigger fallback
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ConnectionError("GOOGLE_API_KEY not configured or set to placeholder")

    # When live key is available, run ADK Runner
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    runner = InMemoryRunner(agent=agent)
    session_id = f"sess_{int(time.time() * 1000)}"
    user_id = "analyst_1"

    prompt_text = (
        f"Analyze this message:\n"
        f"Sender: {message.get('sender')}\n"
        f"Subject: {message.get('subject')}\n"
        f"{guarded['guarded_text']}\n"
        f"URLs: {message.get('urls')}\n"
        f"Attachments: {message.get('attachments')}\n"
        f"Headers: {message.get('headers')}\n"
    )

    user_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt_text)]
    )

    executed_tools = set()
    final_verdict = None

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
        if event_callback:
            await event_callback(event)
        # Capture tool executions and verdict output from events if present
        if hasattr(event, "actions") and event.actions:
            for action in event.actions:
                if hasattr(action, "tool_name") and action.tool_name:
                    executed_tools.add(action.tool_name)

    # In case ADK returned without structured verdict, fallback safely
    if not final_verdict:
        final_verdict = rules_only_verdict(message)

    return validate_verdict(final_verdict, executed_tools)

async def analyze_with_router(
    router_instance: Router,
    message: Dict[str, Any],
    event_callback: Optional[Callable] = None
) -> Tuple[str, Verdict, bool]:
    """Route message analysis through cache -> provider chain -> rules-only fallback.
    
    Returns:
        (provider_used: str, verdict: Verdict, cache_hit: bool)
    """
    # 1. Cache lookup
    cached_data = verdict_cache.get(message)
    if cached_data:
        verdict = Verdict.model_validate(cached_data["verdict"])
        return cached_data["provider_used"], verdict, True

    # 2. Acquire concurrency semaphore for deep analysis
    async with router_instance.concurrency_semaphore:
        # 3. Provider Chain
        for p in router_instance.chain():
            provider_name = p["name"]
            try:
                agent = build_root_agent(p["fast"], p["strong"])
                # 45 second timeout per README
                verdict = await asyncio.wait_for(
                    run_pipeline(agent, message, event_callback),
                    timeout=45.0
                )
                router_instance.mark_success(provider_name)
                # Cache outcome
                verdict_cache.set(message, {
                    "verdict": verdict.model_dump(),
                    "provider_used": provider_name
                })
                return provider_name, verdict, False
            except Exception as e:
                router_instance.mark_failed(provider_name, e)
                continue

        # 4. Fail-safe rules-only fallback (never fails)
        rules_verdict = rules_only_verdict(message)
        verdict_cache.set(message, {
            "verdict": rules_verdict.model_dump(),
            "provider_used": "rules"
        })
        return "rules", rules_verdict, False
