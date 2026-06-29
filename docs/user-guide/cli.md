# CLI

The `godot-ask` command is the main way to interact with Godot RAG from the terminal.

## One-shot question

```powershell
godot-ask "How does CharacterBody2D move_and_slide work?"
```

## Interactive session

```powershell
godot-ask -i
```

Type your questions at the `You:` prompt. Enter `exit`, `quit`, or `q` to leave, or press Ctrl+C.

## Search without OpenAI

Retrieve context from the vector index without calling OpenAI (no API key required):

```powershell
godot-ask --search-only "dodge the creeps player movement"
```

## Choose a model

Override the default model from `.env`:

```powershell
godot-ask --model gpt-4o-mini "What is a TileMapLayer?"
```

## Command reference

| Flag | Description |
|------|-------------|
| `question` | Question to ask (omit for interactive mode) |
| `-i`, `--interactive` | Interactive Q&A session |
| `--search-only` | Local retrieval only; no OpenAI call |
| `--model` | OpenAI model name (default: `OPENAI_MODEL` env or `gpt-5-nano`) |
