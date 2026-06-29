"""Godot expert LangChain agent with RAG tool."""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from scripts.ingest.retriever import format_context_for_prompt, retrieve_for_agent

DEFAULT_MODEL = "gpt-5-nano"

SYSTEM_PROMPT = """You are a Godot 4.x expert coding assistant.

Use the `search_godot_docs` tool to look up official documentation and demo project
examples before answering technical questions. Ground your answers in the retrieved
material and mention relevant file paths or class names when helpful.

If the tool returns no useful context, say what is missing instead of guessing."""


@tool
def search_godot_docs(query: str) -> str:
    """Search Godot 4 documentation and demo projects for explanations, API reference, and code examples."""
    context = retrieve_for_agent(query)
    return format_context_for_prompt(context)


@lru_cache(maxsize=4)
def _build_agent_graph(*, model: str):
    """Create the LangChain agent graph (cached per model)."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key. "
            "See docs/API_KEYS.md for details."
        )

    llm = ChatOpenAI(model=model, temperature=0)
    return create_agent(
        llm,
        tools=[search_godot_docs],
        system_prompt=SYSTEM_PROMPT,
    )


def build_agent(*, model: str | None = None):
    """Create the LangChain agent graph (cached)."""
    load_dotenv()
    model_name = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    return _build_agent_graph(model=model_name)


class GodotAgent:
    """High-level wrapper for the Godot RAG LangChain agent."""

    def __init__(self, *, model: str | None = None) -> None:
        load_dotenv()
        self.model = model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
        self._graph = None

    @property
    def graph(self):
        if self._graph is None:
            self._graph = build_agent(model=self.model)
        return self._graph

    def ask(self, question: str) -> str:
        """Ask a question and return the answer text."""
        return ask(question, model=self.model)["answer"]

    def invoke(self, question: str) -> dict:
        """Ask a question and return answer text plus full message history."""
        return ask(question, model=self.model)


def ask(question: str, *, model: str | None = None) -> dict:
    """Ask the Godot RAG agent a question and return messages + final text."""
    agent = build_agent(model=model)
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    messages = result.get("messages", [])
    final_text = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            final_text = msg.content if isinstance(msg.content, str) else str(msg.content)
            break
    return {"question": question, "answer": final_text, "messages": messages}


def main() -> int:
    from godot_rag.cli import ask_main

    return ask_main()


if __name__ == "__main__":
    raise SystemExit(main())
