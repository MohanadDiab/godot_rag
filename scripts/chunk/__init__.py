"""Runtime paths and chunk schema for Godot RAG."""

from scripts.chunk.config import (
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
    GODOT_VERSION,
    ensure_data_dirs,
    get_paths,
)
from scripts.chunk.schema import Chunk

__all__ = [
    "CHROMA_COLLECTION_NAME",
    "Chunk",
    "EMBEDDING_MODEL",
    "GODOT_VERSION",
    "ensure_data_dirs",
    "get_paths",
]
