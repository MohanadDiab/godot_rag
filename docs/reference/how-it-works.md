# How it works

## RAG engine

| Layer | Technology | Details |
|-------|------------|---------|
| **Vector store** | [ChromaDB](https://www.trychroma.com/) | Persistent HNSW index in `data/chroma/` (`godot_rag` collection) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | 384-dim, runs locally via HuggingFace — no embedding API key needed |
| **Corpus** | Godot 4.x docs + official demos | ~29k chunks: 28k docs, 1.5k demos |
| **Agent** | LangChain + OpenAI | Single `search_godot_docs` tool; answers grounded in retrieved context |

## Chunking

Chunks were built in four phases: docs → demos → cross-linking → merge. The resulting index is **pre-built** and shipped in this repository.

### Documentation

- **Class reference** (`classes/class_*.rst`) — **coarse** chunks (class overview, property/method lists) and **fine** chunks (individual methods, properties, signals)
- **Tutorials & getting started** — section-based chunks; long sections pass through LangChain's **SemanticChunker** at embedding-similarity breakpoints
- **Fallback** — `RecursiveCharacterTextSplitter` (4,000 char max, 200 char overlap) for shorter text

### Demo projects

| Role | Sources |
|------|---------|
| `code` / `shader` | `.gd`, `.cs`, `.gdshader`, `.glsl` |
| `scene` / `resource` | `.tscn`, `.tres` |
| `project_overview` | `project.godot`, README sections |
| Long scripts (>300 lines) | Optional semantic split |

### Cross-linking

Docs and demos are connected via class names, file paths, and manual overrides. ~15k chunks carry `related_ids` so retrieval can pull linked context beyond the initial vector hits.

## Retrieval

The agent retriever (`search_godot_docs`) uses:

1. **Query hints** — regex heuristics infer preferred `role` (e.g. `code` for `.gd` queries) and `granularity` (`fine` for method names, `coarse` for conceptual questions)
2. **Multi-slot assembly** — results bucketed into prompt sections: **Documentation** (4), **Example code** (3), **Scenes/resources** (2), **Linked context** (5)
3. **Supplemental searches** — if a slot is thin, targeted follow-up queries fill the gap
4. **Anchor chunks** — known high-value doc+demo pairs (e.g. dodge-the-creeps player) are injected for matching queries

Retrieval runs entirely on your machine. Only the final answer step calls OpenAI.

## Pre-built index

This distribution includes a ready-to-use vector index. Rebuilding the index from source corpora is not part of the public release — the index is maintained and updated with each release of Godot RAG.

## Data layout

| Path | Purpose |
|------|---------|
| `data/chunks.jsonl` | All indexed chunks (metadata + text) |
| `data/chroma/` | ChromaDB persistence directory |
| `data/corpus_stats.json` | Corpus summary statistics |
| `data/link_stats.json` | Cross-link metadata |
