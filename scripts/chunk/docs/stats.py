"""Corpus statistics for chunked documentation."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.chunk.schema import Chunk


def compute_corpus_stats(chunks: list[Chunk]) -> dict[str, Any]:
    lengths = [len(c.text) for c in chunks]
    by_source = Counter(c.source_type for c in chunks)
    by_role = Counter(c.role for c in chunks)
    by_granularity = Counter(c.granularity or "none" for c in chunks)
    by_language = Counter(c.language or "none" for c in chunks)
    with_related = sum(1 for c in chunks if c.related_ids)

    return {
        "total_chunks": len(chunks),
        "by_source_type": dict(by_source),
        "by_role": dict(by_role),
        "by_granularity": dict(by_granularity),
        "by_language": dict(by_language),
        "chunks_with_related_ids": with_related,
        "text_length": {
            "min": min(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "avg": round(sum(lengths) / len(lengths), 1) if lengths else 0,
        },
        "top_20_largest": sorted(
            [{"chunk_id": c.chunk_id, "length": len(c.text)} for c in chunks],
            key=lambda x: x["length"],
            reverse=True,
        )[:20],
    }


def write_corpus_stats(chunks: list[Chunk], path: Path) -> dict[str, Any]:
    stats = compute_corpus_stats(chunks)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    return stats
