# Godot RAG

[![Documentation](https://img.shields.io/badge/docs-Read%20the%20Docs-blue)](https://godot-rag.readthedocs.io/en/latest/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**Web chat assistant for Godot 4.x** — ask questions in the browser, grounded in official docs and demo projects.

![Demo: using the Godot RAG web chat](docs/assets/videos/pres.gif)

## Quick start

```powershell
git lfs install
git clone https://github.com/MohanadDiab/godot_rag.git
cd godot_rag
python -m venv .venv
.\.venv\Scripts\pip install -e .
cd web/ui && npm install && npm run build && cd ../..
godot-web
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and add your OpenAI API key in the top bar.

## Features

- Streaming chat with session history and example prompts
- Syntax-highlighted code blocks with copy
- Local RAG over ~29k Godot 4.x doc and demo chunks
- Live agent status (retrieving docs, writing answer, timer)

## Also available

- **CLI:** `godot-ask "How does move_and_slide work?"`
- **Python API:** `from godot_rag import ask, search, GodotAgent`
- **Dev mode:** `godot-web --dev` for UI hot reload

## Documentation

**[godot-rag.readthedocs.io](https://godot-rag.readthedocs.io/en/latest/)** — [Quick start](https://godot-rag.readthedocs.io/en/latest/getting-started/quick-start/), [Web UI](https://godot-rag.readthedocs.io/en/latest/user-guide/web-ui/), [API keys](https://godot-rag.readthedocs.io/en/latest/getting-started/api-keys/)

## License

MIT — see [LICENSE](LICENSE). Indexed content is from [Godot docs](https://github.com/godotengine/godot-docs) and [demo projects](https://github.com/godotengine/godot-demo-projects).
