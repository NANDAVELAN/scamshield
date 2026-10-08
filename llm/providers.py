"""LLM Provider chain definitions for ScamShield."""
import os
from typing import List, Dict, Any
from google.adk.models.lite_llm import LiteLlm

def get_provider_chain() -> List[Dict[str, Any]]:
    """Returns the ordered provider fallback chain."""
    return [
        {
            "name": "gemini-pro",
            "fast": "gemini-2.5-flash",
            "strong": "gemini-2.5-pro",
            "cloud": True
        },
        {
            "name": "gemini-flash",
            "fast": "gemini-2.5-flash",
            "strong": "gemini-2.5-flash",
            "cloud": True
        },
        {
            "name": "openrouter",
            "cloud": True,
            "fast": LiteLlm(model=os.getenv("OPENROUTER_FAST_MODEL", "openrouter/google/gemini-2.0-flash-001")),
            "strong": LiteLlm(model=os.getenv("OPENROUTER_STRONG_MODEL", "openrouter/google/gemini-2.0-flash-001"))
        },
        {
            "name": "ollama",
            "cloud": False,
            "fast": LiteLlm(model=os.getenv("OLLAMA_MODEL", "ollama_chat/qwen2.5:7b")),
            "strong": LiteLlm(model=os.getenv("OLLAMA_MODEL", "ollama_chat/qwen2.5:7b"))
        }
    ]

CHAIN = get_provider_chain()
