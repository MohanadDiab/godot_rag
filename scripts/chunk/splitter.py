"""Text splitting utilities for chunk pipelines."""

from __future__ import annotations

from scripts.chunk.config import CHUNK_OVERLAP_CHARS, MAX_CHUNK_CHARS
from scripts.chunk.schema import Chunk


def split_text_by_size(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            break_at = text.rfind("\n\n", start, end)
            if break_at > start + size // 2:
                end = break_at
        parts.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [p for p in parts if p]


def split_oversized_chunks(chunks: list[Chunk]) -> list[Chunk]:
    """Split chunks that exceed MAX_CHUNK_CHARS."""
    result: list[Chunk] = []
    for chunk in chunks:
        if len(chunk.text) <= MAX_CHUNK_CHARS:
            result.append(chunk)
            continue
        parts = split_text_by_size(chunk.text, MAX_CHUNK_CHARS, CHUNK_OVERLAP_CHARS)
        if len(parts) <= 1:
            result.append(chunk)
            continue
        for i, part in enumerate(parts):
            if not part.strip():
                continue
            result.append(
                Chunk(
                    chunk_id=f"{chunk.chunk_id}:split_{i}",
                    text=part,
                    source_type=chunk.source_type,
                    role=chunk.role,
                    granularity=chunk.granularity,
                    language=chunk.language,
                    godot_version=chunk.godot_version,
                    hierarchy=chunk.hierarchy + [f"split_{i}"],
                    parent_id=chunk.chunk_id,
                    file_path=chunk.file_path,
                    title=f"{chunk.title} (split {i + 1})",
                    related_ids=list(chunk.related_ids),
                )
            )
    return result
