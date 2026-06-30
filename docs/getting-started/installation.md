# Installation

## Prerequisites

| Requirement | Purpose |
|-------------|---------|
| **Python 3.11+** | Backend, RAG engine, `godot-web` |
| **Git LFS** | Vector index and chunk files |
| **Node.js (LTS)** | Build the web UI once (`npm install && npm run build`) |
| **OpenAI API key** | Agent answers (enter in web UI top bar or `.env` for CLI) |

## Clone the repository

```powershell
git lfs install
git clone https://github.com/MohanadDiab/godot_rag.git
cd godot_rag
git lfs pull
```

## Python environment

From the repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

This installs the web server, RAG engine, and `godot-ask` CLI together.

## Build the web UI

```powershell
cd web/ui
npm install
npm run build
cd ../..
```

## Environment variables (optional for web UI)

For CLI use or a default model, copy `.env.example` to `.env`:

```powershell
copy .env.example .env
```

See [API keys](api-keys.md). The web UI can use the top bar instead of `.env`.

## Verify

Start the app:

```powershell
godot-web
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

For a faster path, see [Quick start](quick-start.md).

## What's included

| Path | Purpose |
|------|---------|
| `data/chroma/` | Pre-built vector index (required) |
| `data/chunks.jsonl` | Indexed chunk source (LFS) |
| `web/ui/` | React chat interface |
| `scripts/` | Agent and retrieval engine |
| `godot_rag/` | Python package and `godot-ask` CLI |

No Godot source repos are required — the index is already built.
