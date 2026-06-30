# Advanced — CLI

`godot-ask` is a terminal interface to the same RAG agent as the web UI. Use it for scripts, automation, or when you prefer the shell.

## One-shot question

```powershell
godot-ask "How does CharacterBody2D move_and_slide work?"
```

Requires `OPENAI_API_KEY` in `.env` or your environment — see [API keys](../getting-started/api-keys.md).

## Interactive session

```powershell
godot-ask -i
```

## Search without OpenAI

Local vector retrieval only (no API key):

```powershell
godot-ask --search-only "dodge the creeps player movement"
```

## Choose a model

```powershell
godot-ask --model gpt-4o-mini "What is a TileMapLayer?"
```

## Options

| Flag | Description |
|------|-------------|
| `question` | Question to ask (omit for interactive mode) |
| `-i`, `--interactive` | Interactive Q&A |
| `--search-only` | Retrieval only; no OpenAI |
| `--model` | OpenAI model name |

For the primary browser experience, see [Web UI](../user-guide/web-ui.md).
