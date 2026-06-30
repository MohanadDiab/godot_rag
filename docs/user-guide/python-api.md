# Advanced — Python API

Programmatic access to the same RAG engine that powers the web UI and `godot-ask`.

```python
from godot_rag import ask, search, GodotAgent
```

## One-shot question

```python
result = ask("How is player movement implemented in dodge the creeps?")
print(result["answer"])
```

## Agent class

```python
agent = GodotAgent()
print(agent.ask("What is a TileMapLayer?"))
```

## Retrieval only (no API key)

```python
context = search("OpenXR action map")
print(context)
```

## Streaming (web backend)

```python
from godot_rag import stream_ask

async def run():
    messages = [{"role": "user", "content": "How does move_and_slide work?"}]
    async for event in stream_ask(messages, api_key="sk-..."):
        if event["type"] == "token":
            print(event["content"], end="", flush=True)
```

Used by the FastAPI `/api/chat` endpoint in `web/api/`.

## Exports

| Name | Description |
|------|-------------|
| `ask` | One-shot agent question |
| `search` | Local retrieval |
| `GodotAgent` | Agent wrapper |
| `stream_ask` | Async SSE events for the web UI |
| `retrieve_for_agent` | Multi-slot retrieval |
| `format_context_for_prompt` | Format context as prompt text |

For day-to-day use, prefer [Web UI](../user-guide/web-ui.md) or [CLI](cli.md).
