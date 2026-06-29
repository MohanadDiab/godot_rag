# Python API

```python
from godot_rag import ask, search, GodotAgent
```

## Functional API

```python
result = ask("How is player movement implemented in dodge the creeps?")
print(result["answer"])
```

`ask()` returns a dict with `question`, `answer`, and `messages`.

## Class-based API

```python
agent = GodotAgent()
print(agent.ask("What is a TileMapLayer?"))

# Custom model
agent = GodotAgent(model="gpt-4o-mini")
```

## Retrieval only (no API key)

```python
from godot_rag import search

# Formatted text for an LLM prompt (default)
context = search("OpenXR action map")
print(context)

# Raw structured context
from godot_rag import retrieve_for_agent, format_context_for_prompt

ctx = retrieve_for_agent("dodge the creeps player")
print(format_context_for_prompt(ctx))
```

With `prompt=False`, `search()` returns the raw `AgentContext` object:

```python
ctx = search("TileMapLayer", prompt=False)
```

## Streaming (web UI backend)

```python
from godot_rag import stream_ask

async def run():
    messages = [{"role": "user", "content": "How does move_and_slide work?"}]
    async for event in stream_ask(messages, api_key="sk-..."):
        if event["type"] == "token":
            print(event["content"], end="", flush=True)
```

Used by the FastAPI `/api/chat` SSE endpoint in `web/api/`.

## Exports

| Name | Description |
|------|-------------|
| `ask` | One-shot agent question |
| `search` | Local retrieval with optional prompt formatting |
| `GodotAgent` | Stateful agent wrapper |
| `stream_ask` | Async streaming events for the web UI |
| `retrieve_for_agent` | Multi-slot retrieval |
| `format_context_for_prompt` | Format `AgentContext` as prompt text |
| `AgentContext` | Structured retrieval result |
