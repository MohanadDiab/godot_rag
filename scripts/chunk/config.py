"""Runtime paths and settings for Godot RAG."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
CHROMA_PERSIST_DIR = DATA_DIR / "chroma"

GODOT_VERSION = "4.x"
CHROMA_COLLECTION_NAME = "godot_rag"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@dataclass(frozen=True)
class Paths:
    """Resolved paths used at runtime."""

    root: Path
    data: Path
    chroma_persist: Path


def get_paths() -> Paths:
    return Paths(
        root=ROOT_DIR,
        data=DATA_DIR,
        chroma_persist=CHROMA_PERSIST_DIR,
    )


def ensure_data_dirs() -> None:
    """Create data directories if they do not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
