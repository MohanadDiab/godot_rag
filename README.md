# Godot RAG

A retrieval-augmented assistant for **Godot 4.x**. It searches official documentation and demo projects via ChromaDB, then answers questions with a LangChain agent backed by OpenAI.

The vector index is **pre-built** in this repo (`data/chroma/`, ~29k chunks). After install and an API key, you can ask questions immediately — no need to clone Godot docs or demos unless you rebuild the index.

## RAG engine

| Layer | Technology | Details |
|-------|------------|---------|
| **Vector store** | [ChromaDB](https://www.trychroma.com/) | Persistent HNSW index in `data/chroma/` (`godot_rag` collection) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | 384-dim, runs locally via HuggingFace — no embedding API key needed |
| **Corpus** | Godot 4.x docs + official demos | ~29k chunks: 28k docs, 1.5k demos (`getting_started/`, `tutorials/`, `classes/`, demo `.gd`/`.cs`/`.tscn`/`.tres`) |
| **Agent** | LangChain + OpenAI | Single `search_godot_docs` tool; answers grounded in retrieved context |

### Chunking

Chunks are built in four phases: docs → demos → cross-linking → merge.

**Documentation** is split by document structure first, then semantically where it helps:

- **Class reference** (`classes/class_*.rst`) — **coarse** chunks (class overview, property/method lists) and **fine** chunks (individual methods, properties, signals)
- **Tutorials & getting started** — section-based chunks; long sections (>500 chars) pass through LangChain's **SemanticChunker**, which splits at embedding-similarity breakpoints (95th-percentile threshold)
- **Fallback** — `RecursiveCharacterTextSplitter` (4,000 char max, 200 char overlap) when semantic splitting is skipped (`--no-semantic`) or text is too short

**Demo projects** are chunked by file type with role metadata:

| Role | Sources |
|------|---------|
| `code` / `shader` | `.gd`, `.cs`, `.gdshader`, `.glsl` |
| `scene` / `resource` | `.tscn`, `.tres` |
| `project_overview` | `project.godot`, README sections |
| Long scripts (>300 lines) | Optional semantic split |

**Cross-linking** connects docs ↔ demos (class names, file paths, manual overrides in `link_overrides.json`). ~15k chunks carry `related_ids` so retrieval can pull linked context beyond the initial vector hits.

### Retrieval

Raw vector search (`query`) supports metadata filters (`source_type`, `role`, `language`, `granularity`) and **link expansion** — top hits pull in their `related_ids` neighbors.

The agent retriever (`retrieve` / `search_godot_docs`) goes further:

1. **Query hints** — regex heuristics infer preferred `role` (e.g. `code` for `.gd` queries, `api_ref` for class names) and `granularity` (`fine` for `snake_case` methods, `coarse` for "How does X work?")
2. **Multi-slot assembly** — results bucketed into separate prompt sections: **Documentation** (4), **Example code** (3), **Scenes/resources** (2), **Linked context** (5)
3. **Supplemental searches** — if a slot is thin, targeted follow-up queries against docs or demos fill the gap
4. **Anchor chunks** — known high-value doc+demo pairs (e.g. dodge-the-creeps player, compute heightmap) are injected for matching queries

Retrieval runs entirely on your machine. Only the final answer step calls OpenAI.

## Features

- Pre-built ChromaDB index over Godot 4.x docs and official demo projects
- Simple CLI: `godot-ask "your question"`
- Python API: `from godot_rag import ask, search, GodotAgent`
- Local retrieval without OpenAI: `search()` or `godot-ask --search-only`
- Full pipeline CLI for re-chunking and re-embedding: `godot-rag`

## Prerequisites

- Python 3.11+
- OpenAI API key (for agent answers only — see [docs/API_KEYS.md](docs/API_KEYS.md))

## Install

> **Git LFS:** This repo stores the vector index and chunks via [Git LFS](https://git-lfs.com/) (files over GitHub's 100 MB limit). Install LFS before cloning:
>
> ```powershell
> git lfs install
> git clone https://github.com/MohanadDiab/godot_rag.git
> ```

```powershell
cd godot_rag
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
```

Copy the environment template and add your key:

```powershell
copy .env.example .env
```

Edit `.env` with your OpenAI API key. Full guide: **[docs/API_KEYS.md](docs/API_KEYS.md)**.

## Ask the agent

**One-shot question:**

```powershell
godot-ask "How does CharacterBody2D move_and_slide work?"
```

**Interactive session:**

```powershell
godot-ask -i
```

**Search without OpenAI** (local vector retrieval only):

```powershell
godot-ask --search-only "dodge the creeps player movement"
```

### Python API

```python
from godot_rag import ask, search, GodotAgent

# Functional API
result = ask("How is player movement implemented in dodge the creeps?")
print(result["answer"])

# Class-based API
agent = GodotAgent()
print(agent.ask("What is a TileMapLayer?"))

# Retrieval only — no API key needed
context = search("OpenXR action map")
print(context)
```

### Inspect retrieval

```powershell
godot-rag retrieve "dodge the creeps player movement" --prompt
godot-rag query "OpenXR action map" -n 5 --text-only
```

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

| Path | Purpose |
|------|---------|
| `data/chunks.jsonl` | Source of truth for all indexed chunks |
| `data/chroma/` | Persisted vector index (`godot_rag` collection) |
| `godot_rag/` | Public Python package and `godot-ask` CLI |
| `scripts/` | Chunking pipeline, ingest, and agent implementation |

## Rebuilding the index

Only needed if you change docs, demos, or chunking logic. Clone the source corpora first:

```powershell
.\scripts\setup_sources.ps1
```

Then rebuild:

```powershell
# Full pipeline: chunk → link → merge → embed (slow)
godot-rag full --no-semantic --rebuild --batch-size 200
```

Or step by step:

```powershell
godot-rag chunk-docs --no-semantic
godot-rag chunk-demos
godot-rag link
godot-rag merge
godot-rag load-chroma --rebuild
```

`godot-docs/` and `godot-demo-projects/` are not shipped in this repo (~500 MB). Use `scripts/setup_sources.ps1` (or `.sh`) to clone them when rebuilding.

## Tests

```powershell
pytest tests/ -q
pytest tests/ -q -m "not integration"   # skip slow Chroma + embedding tests
```

## CLI reference

| Command | Description |
|---------|-------------|
| `godot-ask` | Ask the agent (supports `-i` interactive, `--search-only`) |
| `godot-rag ask` | Same as above via pipeline CLI |
| `godot-rag retrieve` | Multi-slot retrieval for agent context |
| `godot-rag query` | Direct Chroma vector search |
| `godot-rag load-chroma` | Embed `chunks.jsonl` into Chroma |
| `godot-rag full` | Full rebuild: chunk → link → merge → embed |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `OPENAI_API_KEY is not set` | See [docs/API_KEYS.md](docs/API_KEYS.md) |
| Weak answers | Run `godot-rag retrieve "..." --prompt` to check RAG context |
| Model not found | Set `OPENAI_MODEL` in `.env` to a model your account supports |

## License

This project's pipeline code is [MIT](LICENSE). Indexed content comes from [Godot documentation](https://github.com/godotengine/godot-docs) and [demo projects](https://github.com/godotengine/godot-demo-projects) — follow their respective licenses when redistributing derived data.

## Contributing

1. Fork and clone the repo
2. `pip install -e ".[dev]"`
3. Run tests: `pytest tests/ -q -m "not integration"`
4. Open a pull request

Do not commit `.env` or API keys. See [docs/API_KEYS.md](docs/API_KEYS.md).
