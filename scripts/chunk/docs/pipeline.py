"""Documentation chunking pipeline orchestrator."""

from __future__ import annotations

import logging
from pathlib import Path

from scripts.chunk.config import (
    CHUNKS_DOCS_JSONL_PATH,
    CORPUS_STATS_PATH,
    GODOT_DOCS_DIR,
    ensure_data_dirs,
    get_paths,
)
from scripts.chunk.docs.class_ref import chunk_class_ref_file
from scripts.chunk.docs.discovery import discover_doc_files
from scripts.chunk.docs.semantic import apply_semantic_chunking
from scripts.chunk.docs.stats import compute_corpus_stats, write_corpus_stats
from scripts.chunk.docs.tutorial import chunk_tutorial_file
from scripts.chunk.schema import Chunk, write_chunks_jsonl
from scripts.chunk.splitter import split_oversized_chunks

logger = logging.getLogger(__name__)


def chunk_docs(
    *,
    docs_dir: Path | None = None,
    output_path: Path | None = None,
    use_semantic: bool = True,
    write_stats: bool = True,
) -> dict:
    """
    Run the full Phase 1 documentation chunking pipeline.

    Returns a summary dict with discovery counts, chunk stats, and output path.
    """
    ensure_data_dirs()
    paths = get_paths()
    root = docs_dir or GODOT_DOCS_DIR
    out = output_path or paths.chunks_docs_jsonl

    discovery = discover_doc_files(root)
    logger.info(
        "Discovered %d RST files (%d included, %d skipped)",
        discovery.total_rst,
        len(discovery.included),
        len(discovery.skipped),
    )

    all_chunks: list[Chunk] = []
    class_count = 0
    tutorial_count = 0

    for path in discovery.included:
        rel_path = path.relative_to(root).as_posix()
        raw = path.read_text(encoding="utf-8")
        try:
            if rel_path.startswith("classes/"):
                chunks = chunk_class_ref_file(rel_path, raw)
                class_count += 1
            else:
                chunks = chunk_tutorial_file(rel_path, raw)
                tutorial_count += 1
            all_chunks.extend(chunks)
        except Exception:
            logger.exception("Failed to chunk %s", rel_path)
            raise

    pre_semantic_count = len(all_chunks)
    all_chunks = split_oversized_chunks(all_chunks)
    if len(all_chunks) != pre_semantic_count:
        logger.info(
            "Split oversized chunks: %d -> %d structural chunks",
            pre_semantic_count,
            len(all_chunks),
        )
    pre_semantic_count = len(all_chunks)

    if use_semantic:
        logger.info("Applying semantic chunking to %d structural chunks...", pre_semantic_count)
        all_chunks = apply_semantic_chunking(all_chunks, use_semantic=True)
        logger.info("After semantic chunking: %d chunks", len(all_chunks))

    written = write_chunks_jsonl(all_chunks, out)
    logger.info("Wrote %d chunks to %s", written, out)

    stats = compute_corpus_stats(all_chunks)
    if write_stats:
        write_corpus_stats(all_chunks, CORPUS_STATS_PATH)

    return {
        "discovery": {
            "total_rst": discovery.total_rst,
            "included": len(discovery.included),
            "skipped": len(discovery.skipped),
            "class_files": class_count,
            "tutorial_files": tutorial_count,
        },
        "chunks": {
            "structural": pre_semantic_count,
            "final": len(all_chunks),
            "written": written,
        },
        "stats": stats,
        "output_path": str(out),
    }
