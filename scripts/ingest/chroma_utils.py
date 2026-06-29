"""ChromaDB helpers: metadata serialization and embedding setup."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from typing import Any

from scripts.chunk.config import CHROMA_COLLECTION_NAME, EMBEDDING_MODEL
from scripts.chunk.schema import Chunk

_embeddings_warmed = False
_embeddings_lock = threading.Lock()
_embedding_fn = None

ProgressCallback = Callable[[float, str], None]


def embeddings_are_warmed() -> bool:
    return _embeddings_warmed


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
    global _embedding_fn
    if _embedding_fn is None:
        from chromadb.utils import embedding_functions

        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL,
        )
    return _embedding_fn


def warmup_embeddings(progress: ProgressCallback | None = None) -> None:
    """Load the sentence-transformers model used for vector search (first call only)."""
    global _embeddings_warmed

    if _embeddings_warmed:
        return

    with _embeddings_lock:
        if _embeddings_warmed:
            return

        short_name = EMBEDDING_MODEL.rsplit("/", 1)[-1]
        stop = threading.Event()

        def _tick_progress() -> None:
            pct = 0.08
            while not stop.wait(0.35):
                pct = min(0.88, pct + 0.07)
                if progress:
                    progress(pct, f"Downloading & loading {short_name}…")

        if progress:
            progress(0.05, f"Loading embedding model ({short_name})…")

        ticker = threading.Thread(target=_tick_progress, daemon=True)
        ticker.start()
        try:
            embedding_fn = get_embedding_function()
            embedding_fn(["godot rag warmup"])
        finally:
            stop.set()
            ticker.join(timeout=0.2)

        if progress:
            progress(1.0, "Embedding model ready")

        _embeddings_warmed = True
        time.sleep(0)  # yield GIL after heavy load


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
