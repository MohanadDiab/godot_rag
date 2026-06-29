# Godot RAG

[![Documentation](https://img.shields.io/badge/docs-Read%20the%20Docs-blue)](https://godot-rag.readthedocs.io/en/latest/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A retrieval-augmented assistant for **Godot 4.x**. It searches official documentation and demo projects, then answers your questions with an AI agent grounded in that context.

The vector index is **pre-built** (~29k chunks). Clone, add your OpenAI key, and start asking — no setup pipeline required.

## Quick start

```powershell
git lfs install
git clone https://github.com/MohanadDiab/godot_rag.git
cd godot_rag
python -m venv .venv
.\.venv\Scripts\pip install -e .
copy .env.example .env
# Edit .env — add your OPENAI_API_KEY
godot-ask "How does CharacterBody2D move_and_slide work?"
```

## Features

- **CLI** — `godot-ask "your question"` or interactive mode (`-i`)
- **Web UI** — streamed chat with history, code copy, and in-browser API key
- **Python API** — `from godot_rag import ask, search, GodotAgent`
- **Local search** — `godot-ask --search-only` (no OpenAI key needed)

## Web UI

```powershell
pip install -e ".[web]"
godot-web
```

In a second terminal for development: `cd web/ui && npm install && npm run dev` → [localhost:5173](http://localhost:5173).

See the [Web UI guide](https://godot-rag.readthedocs.io/en/latest/user-guide/web-ui/) for production setup.

## Documentation

**Full documentation on Read the Docs:** [godot-rag.readthedocs.io](https://godot-rag.readthedocs.io/en/latest/)

- [Installation](https://godot-rag.readthedocs.io/en/latest/getting-started/installation/)
- [API keys](https://godot-rag.readthedocs.io/en/latest/getting-started/api-keys/)
- [CLI](https://godot-rag.readthedocs.io/en/latest/user-guide/cli/)
- [Python API](https://godot-rag.readthedocs.io/en/latest/user-guide/python-api/)
- [How it works](https://godot-rag.readthedocs.io/en/latest/reference/how-it-works/)

## License

MIT — see [LICENSE](LICENSE). Indexed content is from [Godot docs](https://github.com/godotengine/godot-docs) and [demo projects](https://github.com/godotengine/godot-demo-projects); follow their licenses when redistributing derived data.
