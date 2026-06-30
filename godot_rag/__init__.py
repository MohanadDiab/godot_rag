"""Godot RAG — web chat and Python API for Godot 4.x docs and demos.

Primary interface: ``godot-web`` (local chat UI).
Secondary: ``godot-ask`` CLI and the exports below.
"""

from __future__ import annotations

from scripts.agent.godot_agent import GodotAgent, ask, stream_ask
from scripts.ingest.retriever import (
    AgentContext,
    format_context_for_prompt,
    retrieve_for_agent,
)


def search(
    query: str,
    *,
    prompt: bool = True,
    **kwargs,
) -> str | AgentContext:
    """Search Godot docs and demos without calling OpenAI.

    With ``prompt=True`` (default), returns formatted text for an LLM prompt.
    With ``prompt=False``, returns the raw :class:`AgentContext`.
    """
    context = retrieve_for_agent(query, **kwargs)
    if prompt:
        return format_context_for_prompt(context)
    return context


__all__ = [
    "AgentContext",
    "GodotAgent",
    "ask",
    "stream_ask",
    "format_context_for_prompt",
    "retrieve_for_agent",
    "search",
]

__version__ = "0.1.0"
