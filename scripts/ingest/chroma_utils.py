"""ChromaDB helpers: metadata serialization and embedding setup."""

from __future__ import annotations

import json
from typing import Any

from scripts.chunk.config import CHROMA_COLLECTION_NAME, EMBEDDING_MODEL
from scripts.chunk.schema import Chunk


def chunk_to_chroma_metadata(chunk: Chunk) -> dict[str, str | int | float | bool]:
    """Convert chunk fields to Chroma-compatible metadata (str/int/float/bool only)."""
    meta: dict[str, str | int | float | bool] = {
        "chunk_id": chunk.chunk_id,
        "source_type": chunk.source_type,
        "role": chunk.role,
        "godot_version": chunk.godot_version,
        "file_path": chunk.file_path,
        "title": chunk.title,
        "hierarchy": json.dumps(chunk.hierarchy, ensure_ascii=False),
    }
    if chunk.granularity:
        meta["granularity"] = chunk.granularity
    if chunk.language:
        meta["language"] = chunk.language
    if chunk.parent_id:
        meta["parent_id"] = chunk.parent_id
    if chunk.related_ids:
        meta["related_ids"] = json.dumps(chunk.related_ids, ensure_ascii=False)
    if chunk.link_types:
        meta["link_types"] = json.dumps(chunk.link_types, ensure_ascii=False)
    if chunk.status:
        meta["status"] = chunk.status
    return meta


def parse_related_ids(metadata: dict[str, Any]) -> list[str]:
    raw = metadata.get("related_ids")
    if not raw:
        return []
    if isinstance(raw, list):
        return raw
    return json.loads(raw)


def get_embedding_function():
    """Return Chroma embedding function using the configured sentence-transformers model."""
    from chromadb.utils import embedding_functions

    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL,
    )


def get_chroma_client(persist_dir: str):
    import chromadb

    return chromadb.PersistentClient(path=persist_dir)


def get_or_create_collection(client, *, rebuild: bool = False):
    if rebuild:
        try:
            client.delete_collection(CHROMA_COLLECTION_NAME)
        except Exception:
            pass
    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
