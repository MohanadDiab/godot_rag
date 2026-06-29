"""Merge doc and demo chunk streams with integrity validation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from pathlib import Path

from scripts.chunk.schema import Chunk

logger = logging.getLogger(__name__)


@dataclass
class IntegrityReport:
    missing_parents: list[tuple[str, str]] = field(default_factory=list)
    circular_parents: list[str] = field(default_factory=list)
    missing_demo_overviews: list[tuple[str, str]] = field(default_factory=list)
    duplicate_ids: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.circular_parents
            or self.missing_demo_overviews
            or self.duplicate_ids
        )


def deduplicate_chunks(chunks: list[Chunk]) -> tuple[list[Chunk], int]:
    """Keep one chunk per chunk_id, preferring the longer text body."""
    by_id: dict[str, Chunk] = {}
    for chunk in chunks:
        existing = by_id.get(chunk.chunk_id)
        if existing is None or len(chunk.text) > len(existing.text):
            by_id[chunk.chunk_id] = chunk
    removed = len(chunks) - len(by_id)
    return list(by_id.values()), removed


def merge_chunks(doc_chunks: list[Chunk], demo_chunks: list[Chunk]) -> tuple[list[Chunk], dict]:
    """Combine chunk lists; dedupe within each source, fail on cross-source collisions."""
    doc_deduped, doc_removed = deduplicate_chunks(doc_chunks)
    demo_deduped, demo_removed = deduplicate_chunks(demo_chunks)

    seen: dict[str, Chunk] = {}
    cross_duplicates: list[str] = []

    for chunk in doc_deduped + demo_deduped:
        if chunk.chunk_id in seen:
            cross_duplicates.append(chunk.chunk_id)
            continue
        seen[chunk.chunk_id] = chunk

    if cross_duplicates:
        raise ValueError(
            f"Cross-source chunk_id collisions ({len(cross_duplicates)}): "
            f"{cross_duplicates[:10]}"
        )

    meta = {
        "doc_duplicates_removed": doc_removed,
        "demo_duplicates_removed": demo_removed,
    }
    return list(seen.values()), meta


def repair_chunks(chunks: list[Chunk]) -> tuple[list[Chunk], dict[str, int]]:
    """Fix dangling parent_id and related_ids after deduplication or splitting."""
    by_id = {c.chunk_id: c for c in chunks}
    stats = {"parent_nulled": 0, "related_pruned": 0}
    repaired: list[Chunk] = []

    for chunk in chunks:
        parent_id = chunk.parent_id
        if parent_id and parent_id not in by_id:
            parent_id = None
            stats["parent_nulled"] += 1

        related_ids = [rid for rid in chunk.related_ids if rid in by_id]
        stats["related_pruned"] += len(chunk.related_ids) - len(related_ids)
        link_types = {k: v for k, v in chunk.link_types.items() if k in related_ids}

        if (
            parent_id != chunk.parent_id
            or related_ids != chunk.related_ids
            or link_types != chunk.link_types
        ):
            chunk = replace(
                chunk,
                parent_id=parent_id,
                related_ids=related_ids,
                link_types=link_types,
            )
        repaired.append(chunk)

    return repaired, stats


def validate_integrity(chunks: list[Chunk], *, strict: bool = True) -> IntegrityReport:
    """Verify parent-child relationships across the merged corpus."""
    report = IntegrityReport()
    by_id = {c.chunk_id: c for c in chunks}

    for chunk in chunks:
        if chunk.parent_id and chunk.parent_id not in by_id:
            report.missing_parents.append((chunk.chunk_id, chunk.parent_id))

        if chunk.parent_id and _has_parent_cycle(chunk.chunk_id, by_id):
            report.circular_parents.append(chunk.chunk_id)

        if chunk.source_type == "demo" and chunk.parent_id:
            overview_id = _demo_overview_id(chunk)
            if (
                overview_id
                and overview_id not in by_id
                and chunk.parent_id == overview_id
            ):
                report.missing_demo_overviews.append((chunk.chunk_id, overview_id))

    if strict and not report.ok:
        problems = []
        if report.duplicate_ids:
            problems.append(f"{len(report.duplicate_ids)} duplicate ids")
        if report.circular_parents:
            problems.append(f"{len(report.circular_parents)} parent cycles")
        if report.missing_demo_overviews:
            problems.append(f"{len(report.missing_demo_overviews)} missing demo overviews")
        raise ValueError("Integrity check failed: " + ", ".join(problems))

    if report.missing_parents:
        logger.warning(
            "%d chunks have missing parent_id (often from split/deduped parents)",
            len(report.missing_parents),
        )

    return report


def _has_parent_cycle(chunk_id: str, by_id: dict[str, Chunk]) -> bool:
    visited: set[str] = set()
    current: str | None = chunk_id
    while current:
        if current in visited:
            return True
        visited.add(current)
        parent = by_id.get(current)
        if not parent or not parent.parent_id:
            return False
        current = parent.parent_id
    return False


def _demo_overview_id(chunk: Chunk) -> str | None:
    if len(chunk.hierarchy) < 2:
        return None
    return f"demo:{chunk.hierarchy[0]}/{chunk.hierarchy[1]}"


def merge_and_write(
    *,
    docs_jsonl: Path | None = None,
    demos_jsonl: Path | None = None,
    output_jsonl: Path | None = None,
    stats_path: Path | None = None,
    strict: bool = True,
) -> dict:
    """Merge linked doc + demo chunks into data/chunks.jsonl with validation."""
    from scripts.chunk.config import (
        CHUNKS_DEMOS_JSONL_PATH,
        CHUNKS_DOCS_JSONL_PATH,
        CHUNKS_JSONL_PATH,
        CORPUS_STATS_PATH,
        ensure_data_dirs,
        get_paths,
    )
    from scripts.chunk.docs.stats import compute_corpus_stats, write_corpus_stats
    from scripts.chunk.schema import read_chunks_jsonl, write_chunks_jsonl

    ensure_data_dirs()
    paths = get_paths()
    docs_path = docs_jsonl or paths.chunks_docs_jsonl
    demos_path = demos_jsonl or paths.chunks_demos_jsonl
    out_path = output_jsonl or paths.chunks_jsonl
    stats_out = stats_path or paths.corpus_stats

    if not docs_path.exists():
        raise FileNotFoundError(f"Missing docs chunks: {docs_path}")
    if not demos_path.exists():
        raise FileNotFoundError(f"Missing demo chunks: {demos_path}")

    doc_chunks = read_chunks_jsonl(docs_path)
    demo_chunks = read_chunks_jsonl(demos_path)
    merged, dedupe_meta = merge_chunks(doc_chunks, demo_chunks)
    if dedupe_meta["doc_duplicates_removed"] or dedupe_meta["demo_duplicates_removed"]:
        logger.warning(
            "Removed duplicate chunk_ids (doc=%d, demo=%d)",
            dedupe_meta["doc_duplicates_removed"],
            dedupe_meta["demo_duplicates_removed"],
        )
    merged, repair_meta = repair_chunks(merged)
    if repair_meta["parent_nulled"] or repair_meta["related_pruned"]:
        logger.info(
            "Repaired chunk graph (parents_nulled=%d, related_pruned=%d)",
            repair_meta["parent_nulled"],
            repair_meta["related_pruned"],
        )
    integrity = validate_integrity(merged, strict=strict)

    written = write_chunks_jsonl(merged, out_path)
    stats = write_corpus_stats(merged, stats_out)

    return {
        "input": {
            "docs_chunks": len(doc_chunks),
            "demo_chunks": len(demo_chunks),
            "deduplication": dedupe_meta,
            "repair": repair_meta,
        },
        "merged_chunks": len(merged),
        "written": written,
        "integrity": {
            "ok": integrity.ok,
            "missing_parents": len(integrity.missing_parents),
            "circular_parents": len(integrity.circular_parents),
            "missing_demo_overviews": len(integrity.missing_demo_overviews),
        },
        "stats": stats,
        "output_path": str(out_path),
        "stats_path": str(stats_out),
    }
