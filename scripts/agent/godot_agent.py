"""Godot expert LangChain agent with RAG tool."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from functools import lru_cache

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from scripts.chunk.config import EMBEDDING_MODEL
from scripts.ingest.chroma_utils import embeddings_are_warmed, warmup_embeddings
from scripts.ingest.retriever import format_context_for_prompt, retrieve_for_agent

DEFAULT_MODEL = "gpt-5-nano"
SEARCH_TOOL_NAME = "search_godot_docs"

SYSTEM_PROMPT = """You are a Godot 4.x expert coding assistant.

Use the `search_godot_docs` tool to look up official documentation and demo project
examples before answering technical questions. Ground your answers in the retrieved
material and mention relevant file paths or class names when helpful.

If the tool returns no useful context, say what is missing instead of guessing."""


@tool
def search_godot_docs(query: str) -> str:
    """Search Godot 4 documentation and demo projects for explanations, API reference, and code examples."""
    warmup_embeddings()
    context = retrieve_for_agent(query)
    return format_context_for_prompt(context)


def _resolve_api_key(api_key: str | None = None) -> str:
    load_dotenv()
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key. "
            "See https://godot-rag.readthedocs.io/en/latest/getting-started/api-keys/ for details."
        )
    return key


def _resolve_model(model: str | None = None) -> str:
    load_dotenv()
    return model or os.getenv("OPENAI_MODEL", DEFAULT_MODEL)


@lru_cache(maxsize=8)
def _build_agent_graph(*, model: str, api_key: str):
    """Create the LangChain agent graph (cached per model + key)."""
    llm = ChatOpenAI(model=model, temperature=0, api_key=api_key)
    return create_agent(
        llm,
        tools=[search_godot_docs],
        system_prompt=SYSTEM_PROMPT,
    )


def build_agent(*, model: str | None = None, api_key: str | None = None):
    """Create the LangChain agent graph (cached)."""
    model_name = _resolve_model(model)
    key = _resolve_api_key(api_key)
    return _build_agent_graph(model=model_name, api_key=key)


def messages_to_lc(messages: list[dict[str, str]]) -> list[HumanMessage | AIMessage]:
    """Convert chat API messages to LangChain message objects."""
    result: list[HumanMessage | AIMessage] = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "assistant":
            result.append(AIMessage(content=content))
        else:
            result.append(HumanMessage(content=content))
    return result


def extract_final_answer(messages: list) -> str:
    """Return the last non-empty assistant text from a message list."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return ""


class GodotAgent:
    """High-level wrapper for the Godot RAG LangChain agent."""

    def __init__(self, *, model: str | None = None, api_key: str | None = None) -> None:
        load_dotenv()
        self.model = _resolve_model(model)
        self.api_key = api_key
        self._graph = None

    @property
    def graph(self):
        if self._graph is None:
            self._graph = build_agent(model=self.model, api_key=self.api_key)
        return self._graph

    def ask(self, question: str) -> str:
        """Ask a question and return the answer text."""
        return ask(question, model=self.model, api_key=self.api_key)["answer"]

    def invoke(self, question: str) -> dict:
        """Ask a question and return answer text plus full message history."""
        return ask(question, model=self.model, api_key=self.api_key)


def ask(
    question: str,
    *,
    model: str | None = None,
    api_key: str | None = None,
) -> dict:
    """Ask the Godot RAG agent a question and return messages + final text."""
    agent = build_agent(model=model, api_key=api_key)
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    messages = result.get("messages", [])
    return {
        "question": question,
        "answer": extract_final_answer(messages),
        "messages": messages,
    }


async def stream_ask(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    api_key: str | None = None,
) -> AsyncIterator[dict]:
    """Stream agent events for the web UI (tokens, tool status, done, errors)."""
    try:
        resolved_key = _resolve_api_key(api_key)
    except RuntimeError as exc:
        yield {"type": "error", "message": str(exc)}
        return

    model_name = _resolve_model(model)
    lc_messages = messages_to_lc(messages)

    if not embeddings_are_warmed():
        yield {
            "type": "embeddings_start",
            "model": EMBEDDING_MODEL,
        }
        loop = asyncio.get_running_loop()
        progress_queue: asyncio.Queue[tuple[float, str] | None] = asyncio.Queue()

        def _on_progress(pct: float, message: str) -> None:
            loop.call_soon_threadsafe(
                progress_queue.put_nowait,
                (pct, message),
            )

        async def _run_warmup() -> None:
            await loop.run_in_executor(None, lambda: warmup_embeddings(_on_progress))
            await progress_queue.put(None)

        warmup_task = asyncio.create_task(_run_warmup())
        while True:
            item = await progress_queue.get()
            if item is None:
                break
            pct, message = item
            yield {
                "type": "embeddings_progress",
                "progress": round(pct * 100, 1),
                "message": message,
            }
        await warmup_task
        yield {"type": "embeddings_ready"}

    agent = build_agent(model=model_name, api_key=resolved_key)

    try:
        stream = await agent.astream_events({"messages": lc_messages}, version="v3")
    except Exception as exc:
        yield {"type": "error", "message": str(exc)}
        return

    queue: asyncio.Queue[dict | None] = asyncio.Queue()
    token_parts: list[str] = []
    seen_tool_ids: set[str] = set()

    async def consume_messages() -> None:
        try:
            async for msg_stream in stream.messages:
                async for delta in msg_stream.text:
                    if delta:
                        token_parts.append(delta)
                        await queue.put({"type": "token", "content": delta})
        except Exception as exc:
            await queue.put({"type": "error", "message": str(exc)})
        finally:
            await queue.put(None)

    async def consume_values() -> None:
        try:
            async for snapshot in stream.values:
                for msg in snapshot.get("messages", []):
                    if isinstance(msg, AIMessage) and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            name = tool_call.get("name")
                            tool_id = tool_call.get("id") or name
                            if name == SEARCH_TOOL_NAME and tool_id not in seen_tool_ids:
                                seen_tool_ids.add(tool_id)
                                await queue.put({"type": "tool_start", "tool": SEARCH_TOOL_NAME})
                    if isinstance(msg, ToolMessage) and msg.name == SEARCH_TOOL_NAME:
                        await queue.put({"type": "tool_end", "tool": SEARCH_TOOL_NAME})
        except Exception:
            pass
        finally:
            await queue.put(None)

    msg_task = asyncio.create_task(consume_messages())
    values_task = asyncio.create_task(consume_values())

    finished = 0
    while finished < 2:
        item = await queue.get()
        if item is None:
            finished += 1
            continue
        if item.get("type") == "error":
            yield item
            await asyncio.gather(msg_task, values_task, return_exceptions=True)
            return
        yield item

    await asyncio.gather(msg_task, values_task, return_exceptions=True)

    final_text = "".join(token_parts)
    try:
        output = await stream.output
        if output:
            final_text = extract_final_answer(output.get("messages", [])) or final_text
    except Exception:
        pass

    yield {"type": "done", "content": final_text}


def main() -> int:
    from godot_rag.cli import ask_main

    return ask_main()


if __name__ == "__main__":
    raise SystemExit(main())
