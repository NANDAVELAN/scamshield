"""Google ADK agent graph for ScamShield multi-agent investigation."""
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
from .schemas import Verdict
from .prompts import (
    EXTRACTOR_PROMPT,
    URL_PROMPT,
    SENDER_PROMPT,
    ATTACH_PROMPT,
    CONTENT_PROMPT,
    VERDICT_PROMPT,
    INCIDENT_PROMPT
)
from .tools.entities import extract_entities
from .tools.url_tools import check_lookalike, get_domain_age, check_blocklist
from .tools.sender_tools import get_sender_reputation, check_email_auth
from .tools.attachment_tools import analyze_attachment
from .tools.campaign_tools import link_campaign
from .tools.incident_tools import open_incident, propose_action

def build_root_agent(fast_model, strong_model):
    """Build the ScamShield root sequential agent with specialist parallel investigators.
    
    fast_model: Gemini model identifier string or LiteLlm object for rapid tool-heavy tasks.
    strong_model: High-capacity Gemini model or LiteLlm object for final verdict synthesis.
    """
    entity_extractor = LlmAgent(
        name="entity_extractor",
        model=fast_model,
        instruction=EXTRACTOR_PROMPT,
        tools=[extract_entities],
        output_key="entities"
    )

    url_inv = LlmAgent(
        name="url_investigator",
        model=fast_model,
        instruction=URL_PROMPT,
        tools=[check_lookalike, get_domain_age, check_blocklist],
        output_key="url_findings"
    )

    sender_inv = LlmAgent(
        name="sender_investigator",
        model=fast_model,
        instruction=SENDER_PROMPT,
        tools=[get_sender_reputation, check_email_auth],
        output_key="sender_findings"
    )

    attach_inv = LlmAgent(
        name="attachment_investigator",
        model=fast_model,
        instruction=ATTACH_PROMPT,
        tools=[analyze_attachment],
        output_key="attachment_findings"
    )

    content_inv = LlmAgent(
        name="content_investigator",
        model=fast_model,
        instruction=CONTENT_PROMPT,
        output_key="content_findings"
    )

    investigators = ParallelAgent(
        name="investigators",
        sub_agents=[url_inv, sender_inv, attach_inv, content_inv]
    )

    verdict = LlmAgent(
        name="verdict_agent",
        model=strong_model,
        instruction=VERDICT_PROMPT,
        output_schema=Verdict,
        output_key="verdict"
    )

    incident = LlmAgent(
        name="incident_agent",
        model=fast_model,
        instruction=INCIDENT_PROMPT,
        tools=[link_campaign, open_incident, propose_action],
        output_key="incident"
    )

    return SequentialAgent(
        name="scamshield_root",
        sub_agents=[entity_extractor, investigators, verdict, incident]
    )

# Root agent export for `adk web` debugging
root_agent = build_root_agent("gemini-2.5-flash", "gemini-2.5-pro")
