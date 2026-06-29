"""Central configuration for the Godot RAG chunking pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Repository root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

GODOT_DOCS_DIR = ROOT_DIR / "godot-docs"
GODOT_DEMOS_DIR = ROOT_DIR / "godot-demo-projects"

DATA_DIR = ROOT_DIR / "data"
CHUNKS_JSONL_PATH = DATA_DIR / "chunks.jsonl"
CHUNKS_DOCS_JSONL_PATH = DATA_DIR / "chunks_docs.jsonl"
CHUNKS_DEMOS_JSONL_PATH = DATA_DIR / "chunks_demos.jsonl"
CORPUS_STATS_PATH = DATA_DIR / "corpus_stats.json"
CHROMA_PERSIST_DIR = DATA_DIR / "chroma"
LINK_OVERRIDES_PATH = ROOT_DIR / "scripts" / "chunk" / "link_overrides.json"

GODOT_VERSION = "4.x"
CHROMA_COLLECTION_NAME = "godot_rag"

# --- Documentation paths ---------------------------------------------------

DOC_INCLUDE_DIRS = (
    "getting_started",
    "tutorials",
    "classes",
)

DOC_EXCLUDE_DIRS = frozenset(
    {
        "community",
        "about",
        "_static",
        "_extensions",
        "_templates",
        "_build",
        ".git",
    }
)

# --- Demo project paths ------------------------------------------------------

DEMO_EXCLUDE_DIR_NAMES = frozenset(
    {
        ".git",
        "screenshots",
    }
)

DEMO_EXCLUDE_FILE_SUFFIXES = frozenset(
    {
        ".import",
        ".uid",
        ".gitattributes",
        ".gitignore",
    }
)

DEMO_EXCLUDE_FILE_NAMES = frozenset(
    {
        "icon.svg",
    }
)

DEMO_INCLUDE_CODE_SUFFIXES = frozenset({".gd", ".cs"})
DEMO_INCLUDE_SHADER_SUFFIXES = frozenset({".gdshader", ".glsl"})
DEMO_INCLUDE_SCENE_SUFFIXES = frozenset({".tscn"})
DEMO_INCLUDE_RESOURCE_SUFFIXES = frozenset({".tres"})

DEMO_INCLUDE_DOC_SUFFIXES = frozenset({".md"})
DEMO_PROJECT_MARKER = "project.godot"

# Binary / asset extensions — never index
DEMO_EXCLUDE_ASSET_SUFFIXES = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".gif",
        ".svg",
        ".ogg",
        ".wav",
        ".mp3",
        ".ttf",
        ".otf",
        ".woff",
        ".woff2",
        ".gltf",
        ".glb",
        ".bin",
        ".exr",
        ".hdr",
        ".fbx",
        ".obj",
        ".blend",
    }
)

# README sections to strip when normalizing
README_EXCLUDE_SECTIONS = frozenset(
    {
        "screenshots",
        "copying",
    }
)

# --- Chunking parameters -----------------------------------------------------

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# To upgrade: change EMBEDDING_MODEL, then `load-chroma --rebuild` (no re-chunk needed).

# Minimum character length before applying semantic chunking
SEMANTIC_CHUNK_MIN_CHARS = 500

# Fallback splitter when semantic chunking is skipped or unavailable
MAX_CHUNK_CHARS = 4000
CHUNK_OVERLAP_CHARS = 200

# Scripts longer than this may be semantically split (line count)
DEMO_SCRIPT_SEMANTIC_SPLIT_LINE_THRESHOLD = 300

# LangChain SemanticChunker defaults
SEMANTIC_BREAKPOINT_THRESHOLD_TYPE = "percentile"
SEMANTIC_BREAKPOINT_THRESHOLD_AMOUNT = 95


@dataclass(frozen=True)
class Paths:
    """Resolved paths used by the pipeline."""

    root: Path
    godot_docs: Path
    godot_demos: Path
    data: Path
    chunks_jsonl: Path
    chunks_docs_jsonl: Path
    chunks_demos_jsonl: Path
    corpus_stats: Path
    chroma_persist: Path
    link_overrides: Path


def get_paths() -> Paths:
    return Paths(
        root=ROOT_DIR,
        godot_docs=GODOT_DOCS_DIR,
        godot_demos=GODOT_DEMOS_DIR,
        data=DATA_DIR,
        chunks_jsonl=CHUNKS_JSONL_PATH,
        chunks_docs_jsonl=CHUNKS_DOCS_JSONL_PATH,
        chunks_demos_jsonl=CHUNKS_DEMOS_JSONL_PATH,
        corpus_stats=CORPUS_STATS_PATH,
        chroma_persist=CHROMA_PERSIST_DIR,
        link_overrides=LINK_OVERRIDES_PATH,
    )


def ensure_data_dirs() -> None:
    """Create output directories if they do not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
