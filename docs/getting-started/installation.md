# Installation

## Prerequisites

- **Python 3.11+**
- **Git LFS** — the vector index and chunk files are stored via [Git LFS](https://git-lfs.com/) (over GitHub's 100 MB limit)
- **OpenAI API key** — required for agent answers only; see [API keys](api-keys.md)

## Clone the repository

Install Git LFS, then clone:

```powershell
git lfs install
git clone https://github.com/MohanadDiab/godot_rag.git
cd godot_rag
```

If you already cloned without LFS, pull the large files:

```powershell
git lfs pull
```

## Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

For the web UI, install the optional extra:

```powershell
pip install -e ".[web]"
```

On Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Environment variables

Copy the template and add your OpenAI key:

```powershell
copy .env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-5-nano
```

Full guide: [API keys](api-keys.md).

## Verify installation

```powershell
godot-ask --search-only "CharacterBody2D move_and_slide"
```

This runs local retrieval only (no API key needed). For a full agent answer:

```powershell
godot-ask "How does CharacterBody2D move_and_slide work?"
```

## What's included

| Path | Purpose |
|------|---------|
| `data/chunks.jsonl` | Source of truth for all indexed chunks |
| `data/chroma/` | Persisted vector index (`godot_rag` collection) |
| `godot_rag/` | Public Python package and `godot-ask` CLI |
| `scripts/` | Agent and retrieval implementation |
| `web/` | FastAPI backend and React chat UI |

The index is pre-built. You do not need to download Godot docs or demo projects to use Godot RAG.
