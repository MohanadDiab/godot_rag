# Godot RAG

A **web chat assistant** for **Godot 4.x**. Ask questions in the browser; answers are grounded in official documentation and demo projects via a local RAG engine and OpenAI.

![Demo: using the Godot RAG web chat](assets/videos/pres.gif)

The vector index is **pre-built** (~29k chunks). Clone, build the UI once, run `godot-web`, and add your API key in the top bar.

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

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and enter your OpenAI API key in the top bar.

Full walkthrough: [Quick start](getting-started/quick-start.md) on Read the Docs.

## Features

- **Web chat UI** — streaming replies, session history, syntax-highlighted code with copy
- **Example prompts** — one-click starters for common Godot topics
- **Local RAG** — ChromaDB + sentence-transformers over ~29k doc and demo chunks
- **Agent activity** — live status while retrieving docs and generating answers

![Assistant reply with a code block](assets/screenshots/chat-code-block.png)

## Also available

| Interface | Command / import |
|-----------|------------------|
| CLI | `godot-ask "your question"` |
| Python API | `from godot_rag import ask, search, GodotAgent` |
| Dev UI hot reload | `godot-web --dev` → [localhost:5173](http://localhost:5173) |

See [Advanced — CLI](user-guide/cli.md) and [Advanced — Python API](user-guide/python-api.md).

## Documentation

**[godot-rag.readthedocs.io](https://godot-rag.readthedocs.io/en/latest/)**

- [Quick start](getting-started/quick-start.md)
- [Web UI](user-guide/web-ui.md)
- [API keys](getting-started/api-keys.md)
- [How it works](reference/how-it-works.md)

## License

MIT — see [LICENSE](https://github.com/MohanadDiab/godot_rag/blob/main/LICENSE). Indexed content is from [Godot documentation](https://github.com/godotengine/godot-docs) and [demo projects](https://github.com/godotengine/godot-demo-projects).
