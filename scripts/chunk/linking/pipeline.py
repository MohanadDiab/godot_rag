"""Cross-linking pipeline orchestrator."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from scripts.chunk.config import (
    CHUNKS_DEMOS_JSONL_PATH,
    CHUNKS_DOCS_JSONL_PATH,
    ensure_data_dirs,
    get_paths,
)
from scripts.chunk.docs.stats import compute_corpus_stats
from scripts.chunk.linking.extract import build_link_graph
from scripts.chunk.linking.inject import inject_links
from scripts.chunk.schema import Chunk, read_chunks_jsonl, write_chunks_jsonl

logger = logging.getLogger(__name__)

LINK_STATS_PATH = get_paths().data / "link_stats.json"


def link_chunks(
    *,
    docs_jsonl: Path | None = None,
    demos_jsonl: Path | None = None,
    write_back: bool = True,
) -> dict:
    """
    Build doc ↔ demo link graph and inject related_ids into chunk files.

    Reads chunks_docs.jsonl and chunks_demos.jsonl, writes them back with links.
    """
    ensure_data_dirs()
    paths = get_paths()
    docs_path = docs_jsonl or paths.chunks_docs_jsonl
    demos_path = demos_jsonl or paths.chunks_demos_jsonl

    if not docs_path.exists():
        raise FileNotFoundError(f"Missing docs chunks: {docs_path}")
    if not demos_path.exists():
        raise FileNotFoundError(f"Missing demo chunks: {demos_path}")

    doc_chunks = read_chunks_jsonl(docs_path)
    demo_chunks = read_chunks_jsonl(demos_path)
    all_chunks = doc_chunks + demo_chunks

    graph = build_link_graph()
    logger.info("Built link graph with %d project links", len(graph.links))

    linked = inject_links(all_chunks, graph)
    doc_linked = [c for c in linked if c.source_type == "doc"]
    demo_linked = [c for c in linked if c.source_type == "demo"]

    with_links = sum(1 for c in linked if c.related_ids)
    if write_back:
        write_chunks_jsonl(doc_linked, docs_path)
        write_chunks_jsonl(demo_linked, demos_path)
        logger.info("Wrote linked chunks to %s and %s", docs_path, demos_path)

    stats = {
        "project_links": len(graph.links),
        "links": [
            {
                "doc_prefixes": link.doc_prefixes,
                "demo_paths": link.demo_paths,
                "link_type": link.link_type,
                "source": link.source,
            }
            for link in graph.links
        ],
        "chunks_total": len(linked),
        "chunks_with_related_ids": with_links,
        "doc_chunks_with_links": sum(1 for c in doc_linked if c.related_ids),
        "demo_chunks_with_links": sum(1 for c in demo_linked if c.related_ids),
    }
    LINK_STATS_PATH.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    return {
        "graph": stats,
        "corpus": compute_corpus_stats(linked),
        "docs_path": str(docs_path),
        "demos_path": str(demos_path),
    }
