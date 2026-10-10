"""Google ADK Multi-Agent investigation graph for ScamShield.
Constructs SequentialAgent with Triage, ParallelAgent (URL, Sender, Attachment), and Verdict Synthesizer.
"""
from typing import Dict, Any, List, Optional
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
from .schemas import Verdict
from .tools import (
    extract_urls,
    expand_short_url,
    lookalike_brand_check,
    domain_age,
    display_name_spoof,
    parse_auth_results,
    reply_to_mismatch,
    attachment_check
)

TRIAGE_PROMPT = """You are the ScamShield Triage Agent.
Assess the incoming alert and determine which deep specialist investigators are needed (URL, Sender, Attachment).
Summarize risk indicators quickly."""

URL_PROMPT = """You are the ScamShield URL Investigator.
Examine extracted links using lookalike brand checks, homoglyph analysis, and domain age.
Report suspicious spoofed domains or shortener redirection threats."""

SENDER_PROMPT = """You are the ScamShield Sender Investigator.
Verify sender identity, display name spoofing, and email authentication (SPF/DKIM).
Report sender impersonation threats."""

ATTACH_PROMPT = """You are the ScamShield Attachment Investigator.
Inspect attached files for double extensions (.pdf.exe), executables (.apk, .exe, .scr), or macro-enabled documents.
Report risky file formats."""

VERDICT_PROMPT = """You are the ScamShield Verdict Synthesizer.
Synthesize the findings from Triage, URL, Sender, and Attachment investigators.
Produce a strict structured Verdict with:
- verdict: "safe", "suspicious", or "scam"
- score: integer from 0 to 100
- action: "allow", "warn", or "block"
- reason: concise 1-sentence explanation for the user
- evidence: object with reflex, url, sender, and attachment summaries."""

def build_scamshield_agent(fast_model: Any, strong_model: Any) -> SequentialAgent:
    """Build the ScamShield Google ADK root sequential agent with specialist parallel investigators."""
    
    triage_agent = LlmAgent(
        name="triage_agent",
        model=fast_model,
        instruction=TRIAGE_PROMPT,
        output_key="triage_findings"
    )

    url_inv = LlmAgent(
        name="url_investigator",
        model=fast_model,
        instruction=URL_PROMPT,
        tools=[extract_urls, expand_short_url, lookalike_brand_check, domain_age],
        output_key="url_findings"
    )

    sender_inv = LlmAgent(
        name="sender_investigator",
        model=fast_model,
        instruction=SENDER_PROMPT,
        tools=[display_name_spoof, parse_auth_results, reply_to_mismatch],
        output_key="sender_findings"
    )

    attach_inv = LlmAgent(
        name="attachment_investigator",
        model=fast_model,
        instruction=ATTACH_PROMPT,
        tools=[attachment_check],
        output_key="attachment_findings"
    )

    investigators = ParallelAgent(
        name="investigators",
        sub_agents=[url_inv, sender_inv, attach_inv]
    )

    verdict_synthesizer = LlmAgent(
        name="verdict_synthesizer",
        model=strong_model,
        instruction=VERDICT_PROMPT,
        output_schema=Verdict,
        output_key="verdict"
    )

    return SequentialAgent(
        name="scamshield_root",
        sub_agents=[triage_agent, investigators, verdict_synthesizer]
    )
