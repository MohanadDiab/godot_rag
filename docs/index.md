# Godot RAG

A retrieval-augmented assistant for **Godot 4.x**. It searches official documentation and demo projects via ChromaDB, then answers questions with a LangChain agent backed by OpenAI.

The vector index is **pre-built** in the repository (`data/chroma/`, ~29k chunks). After install and an API key, you can ask questions immediately.

## Features

- Pre-built ChromaDB index over Godot 4.x docs and official demo projects
- **CLI** — `godot-ask "your question"`
- **Web UI** — streamed chat with history, syntax-highlighted code blocks, and copy
- **Python API** — `from godot_rag import ask, search, GodotAgent`
- **Local search** — `search()` or `godot-ask --search-only` (no OpenAI key required)

## How it works

```
Your question
    → LangChain agent (OpenAI)
        → search_godot_docs tool
            → ChromaDB vector search (all-MiniLM-L6-v2)
            → Link expansion (docs ↔ demos)
            → Context slots: docs | code | scenes
        → Grounded answer
```

Retrieval runs entirely on your machine. Only the final answer step calls OpenAI.

## Quick start

```powershell
git lfs install
git clone https://github.com/MohanadDiab/godot_rag.git
cd godot_rag
python -m venv .venv
.\.venv\Scripts\pip install -e .
copy .env.example .env
# Edit .env with your OpenAI API key
godot-ask "How does CharacterBody2D move_and_slide work?"
```

See [Installation](getting-started/installation.md) for details and the [Web UI](user-guide/web-ui.md) setup.

## License

Pipeline and application code is [MIT](https://github.com/MohanadDiab/godot_rag/blob/main/LICENSE). Indexed content comes from [Godot documentation](https://github.com/godotengine/godot-docs) and [demo projects](https://github.com/godotengine/godot-demo-projects) — follow their respective licenses when redistributing derived data.
