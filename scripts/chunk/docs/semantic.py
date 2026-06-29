"""LangChain semantic chunking for documentation chunks."""

from __future__ import annotations

import logging

from scripts.chunk.config import (
    CHUNK_OVERLAP_CHARS,
    EMBEDDING_MODEL,
    MAX_CHUNK_CHARS,
    SEMANTIC_BREAKPOINT_THRESHOLD_AMOUNT,
    SEMANTIC_BREAKPOINT_THRESHOLD_TYPE,
    SEMANTIC_CHUNK_MIN_CHARS,
)
from scripts.chunk.schema import Chunk

logger = logging.getLogger(__name__)

_splitter = None


def _get_semantic_splitter():
    global _splitter
    if _splitter is not None:
        return _splitter
    try:
        from langchain_experimental.text_splitter import SemanticChunker
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        _splitter = SemanticChunker(
            embeddings,
            breakpoint_threshold_type=SEMANTIC_BREAKPOINT_THRESHOLD_TYPE,
            breakpoint_threshold_amount=SEMANTIC_BREAKPOINT_THRESHOLD_AMOUNT,
        )
    except ImportError:
        logger.warning("langchain_experimental not installed; using recursive fallback splitter")
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        _splitter = RecursiveCharacterTextSplitter(
            chunk_size=MAX_CHUNK_CHARS,
            chunk_overlap=CHUNK_OVERLAP_CHARS,
        )
    return _splitter


def _get_fallback_splitter():
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    return RecursiveCharacterTextSplitter(
        chunk_size=MAX_CHUNK_CHARS,
        chunk_overlap=CHUNK_OVERLAP_CHARS,
    )


def should_semantically_split(chunk: Chunk) -> bool:
    if len(chunk.text) < SEMANTIC_CHUNK_MIN_CHARS:
        return False
    if chunk.granularity == "fine":
        return False
    if chunk.role == "api_ref" and chunk.granularity == "fine":
        return False
    return True


def split_chunk(chunk: Chunk, *, use_semantic: bool = True) -> list[Chunk]:
    """Split a single chunk if it exceeds the semantic threshold."""
    if not should_semantically_split(chunk):
        return [chunk]

    splitter = _get_semantic_splitter() if use_semantic else _get_fallback_splitter()
    try:
        parts = splitter.split_text(chunk.text)
    except Exception as exc:
        logger.warning("Semantic split failed for %s: %s", chunk.chunk_id, exc)
        parts = _get_fallback_splitter().split_text(chunk.text)

    if len(parts) <= 1:
        return [chunk]

    result: list[Chunk] = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        result.append(
            Chunk(
                chunk_id=f"{chunk.chunk_id}:part_{i}",
                text=part,
                source_type=chunk.source_type,
                role=chunk.role,
                granularity=chunk.granularity,
                language=chunk.language,
                godot_version=chunk.godot_version,
                hierarchy=chunk.hierarchy + [f"part_{i}"],
                parent_id=chunk.chunk_id,
                file_path=chunk.file_path,
                title=f"{chunk.title} (part {i + 1})",
                related_ids=list(chunk.related_ids),
            )
        )
    return result or [chunk]


def apply_semantic_chunking(
    chunks: list[Chunk],
    *,
    use_semantic: bool = True,
) -> list[Chunk]:
    """Apply semantic splitting across all eligible chunks."""
    result: list[Chunk] = []
    for chunk in chunks:
        result.extend(split_chunk(chunk, use_semantic=use_semantic))
    return result
