"""Demo project chunking pipeline orchestrator."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from scripts.chunk.config import (
    CHUNKS_DEMOS_JSONL_PATH,
    GODOT_DEMOS_DIR,
    ensure_data_dirs,
    get_paths,
)
from scripts.chunk.demos.discovery import discover_demo_projects
from scripts.chunk.demos.project import chunk_demo_project
from scripts.chunk.docs.stats import compute_corpus_stats
from scripts.chunk.schema import Chunk, write_chunks_jsonl
from scripts.chunk.splitter import split_oversized_chunks

logger = logging.getLogger(__name__)

DEMO_STATS_PATH = get_paths().data / "corpus_stats_demos.json"


def chunk_demos(
    *,
    demos_dir: Path | None = None,
    output_path: Path | None = None,
    write_stats: bool = True,
) -> dict:
    """Run the full Phase 2 demo project chunking pipeline."""
    ensure_data_dirs()
    paths = get_paths()
    root = demos_dir or GODOT_DEMOS_DIR
    out = output_path or paths.chunks_demos_jsonl

    projects = discover_demo_projects(root)
    logger.info("Discovered %d demo projects", len(projects))

    all_chunks: list[Chunk] = []
    skipped_files = 0

    for project in projects:
        try:
            chunks = chunk_demo_project(project)
            all_chunks.extend(chunks)
        except Exception:
            logger.exception("Failed to chunk project %s", project.rel_path)
            raise

    pre_split = len(all_chunks)
    splittable = [c for c in all_chunks if c.role not in ("scene", "resource")]
    preserved = [c for c in all_chunks if c.role in ("scene", "resource")]
    all_chunks = preserved + split_oversized_chunks(splittable)
    if len(all_chunks) != pre_split:
        logger.info("Split oversized demo chunks: %d -> %d", pre_split, len(all_chunks))

    written = write_chunks_jsonl(all_chunks, out)
    logger.info("Wrote %d chunks to %s", written, out)

    stats = compute_corpus_stats(all_chunks)
    if write_stats:
        DEMO_STATS_PATH.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    by_project: dict[str, int] = {}
    for chunk in all_chunks:
        if len(chunk.hierarchy) >= 2:
            key = f"{chunk.hierarchy[0]}/{chunk.hierarchy[1]}"
            by_project[key] = by_project.get(key, 0) + 1

    return {
        "discovery": {
            "projects": len(projects),
        },
        "chunks": {
            "structural": pre_split,
            "final": len(all_chunks),
            "written": written,
        },
        "stats": stats,
        "top_projects_by_chunk_count": dict(
            sorted(by_project.items(), key=lambda x: x[1], reverse=True)[:10]
        ),
        "output_path": str(out),
        "skipped_files": skipped_files,
    }
