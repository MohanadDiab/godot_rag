"""Inject bidirectional related_ids into doc and demo chunks."""

from __future__ import annotations

import re
from dataclasses import replace

from scripts.chunk.linking.graph import LinkGraph, ProjectLink
from scripts.chunk.schema import Chunk


def inject_links(chunks: list[Chunk], graph: LinkGraph) -> list[Chunk]:
    """Return new chunk list with bidirectional related_ids and link_types."""
    by_id = {c.chunk_id: c for c in chunks}
    updates: dict[str, dict] = {}  # chunk_id -> {related_ids: set, link_types: dict}

    def ensure(cid: str) -> None:
        if cid not in updates:
            chunk = by_id[cid]
            updates[cid] = {
                "related_ids": set(chunk.related_ids),
                "link_types": dict(chunk.link_types),
            }

    def add_link(from_id: str, to_id: str, link_type: str) -> None:
        if from_id not in by_id or to_id not in by_id:
            return
        ensure(from_id)
        ensure(to_id)
        updates[from_id]["related_ids"].add(to_id)
        updates[from_id]["link_types"][to_id] = link_type

    demo_by_path = _index_demos_by_path(chunks)
    docs_by_prefix = _index_docs_by_prefix(chunks)

    for project_link in graph.links:
        _inject_project_link(
            project_link,
            chunks,
            demo_by_path,
            docs_by_prefix,
            add_link,
        )

    result: list[Chunk] = []
    for chunk in chunks:
        if chunk.chunk_id not in updates:
            result.append(chunk)
            continue
        upd = updates[chunk.chunk_id]
        result.append(
            replace(
                chunk,
                related_ids=sorted(upd["related_ids"]),
                link_types=upd["link_types"],
            )
        )
    return result


def _index_demos_by_path(chunks: list[Chunk]) -> dict[str, list[Chunk]]:
    index: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        if chunk.source_type != "demo":
            continue
        if len(chunk.hierarchy) >= 2:
            path = f"{chunk.hierarchy[0]}/{chunk.hierarchy[1]}"
            index.setdefault(path, []).append(chunk)
    return index


def _index_docs_by_prefix(chunks: list[Chunk]) -> dict[str, list[Chunk]]:
    index: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        if chunk.source_type != "demo":
            fp = chunk.file_path.replace("\\", "/")
            if fp.endswith(".rst"):
                fp = fp[:-4]
            parts = fp.split("/")
            for i in range(1, len(parts) + 1):
                prefix = "/".join(parts[:i])
                index.setdefault(prefix, []).append(chunk)
    return index


def _inject_project_link(
    link: ProjectLink,
    chunks: list[Chunk],
    demo_by_path: dict[str, list[Chunk]],
    docs_by_prefix: dict[str, list[Chunk]],
    add_link,
) -> None:
    demo_chunks: list[Chunk] = []
    for demo_path in link.demo_paths:
        demo_chunks.extend(demo_by_path.get(demo_path, []))

    doc_chunks: list[Chunk] = []
    seen_doc_ids: set[str] = set()
    for prefix in link.doc_prefixes:
        for chunk in docs_by_prefix.get(prefix, []):
            if not _doc_chunk_in_prefix(chunk, prefix):
                continue
            if chunk.chunk_id in seen_doc_ids:
                continue
            seen_doc_ids.add(chunk.chunk_id)
            doc_chunks.append(chunk)

    if not demo_chunks or not doc_chunks:
        return

    demo_overviews = [c for c in demo_chunks if c.role == "project_overview" and c.parent_id is None]
    demo_code_scenes = [c for c in demo_chunks if c.role in ("code", "scene", "shader", "resource")]
    doc_explanations = [c for c in doc_chunks if c.role == "explanation"]
    doc_indices = [
        c
        for c in doc_explanations
        if c.chunk_id == f"doc:{link.doc_prefixes[0]}" or c.file_path.replace(".rst", "").endswith("index")
    ]
    doc_api = [c for c in doc_chunks if c.role == "api_ref"]

    for doc_chunk in doc_explanations:
        for overview in demo_overviews:
            add_link(doc_chunk.chunk_id, overview.chunk_id, "tutorial_to_demo")
            add_link(overview.chunk_id, doc_chunk.chunk_id, "demo_to_tutorial")

        for demo_file in demo_code_scenes:
            if _demo_file_relevant_to_doc(doc_chunk, demo_file):
                add_link(doc_chunk.chunk_id, demo_file.chunk_id, "tutorial_to_demo")
                add_link(demo_file.chunk_id, doc_chunk.chunk_id, "demo_to_tutorial")

    for doc_chunk in doc_api:
        if not _doc_mentions_demo(doc_chunk, link.demo_paths):
            continue
        for overview in demo_overviews:
            add_link(doc_chunk.chunk_id, overview.chunk_id, "api_to_example")
            add_link(overview.chunk_id, doc_chunk.chunk_id, "demo_to_tutorial")

    for demo_chunk in demo_code_scenes + demo_overviews:
        if demo_chunk.role == "project_overview" and demo_chunk.parent_id is not None:
            continue
        for doc_chunk in doc_explanations:
            if _demo_file_relevant_to_doc(doc_chunk, demo_chunk) or demo_chunk.role == "project_overview":
                add_link(demo_chunk.chunk_id, doc_chunk.chunk_id, "demo_to_tutorial")
                add_link(doc_chunk.chunk_id, demo_chunk.chunk_id, "tutorial_to_demo")

        if demo_chunk.role == "project_overview":
            for doc_chunk in doc_indices[:3]:
                add_link(demo_chunk.chunk_id, doc_chunk.chunk_id, "demo_to_tutorial")
                add_link(doc_chunk.chunk_id, demo_chunk.chunk_id, "tutorial_to_demo")


def _doc_mentions_demo(doc_chunk: Chunk, demo_paths: list[str]) -> bool:
    text = doc_chunk.text.lower()
    for path in demo_paths:
        if path.lower() in text:
            return True
        project_name = path.split("/")[-1]
        if project_name in text:
            return True
    return "godot-demo-projects" in text


def _doc_chunk_in_prefix(chunk: Chunk, prefix: str) -> bool:
    fp = chunk.file_path.replace("\\", "/")
    if fp.endswith(".rst"):
        fp = fp[:-4]
    return fp == prefix or fp.startswith(prefix + "/")


def _demo_file_relevant_to_doc(doc_chunk: Chunk, demo_chunk: Chunk) -> bool:
    if demo_chunk.role not in ("code", "scene", "shader", "resource"):
        return False
    filename = demo_chunk.file_path.split("/")[-1]
    stem = filename.rsplit(".", 1)[0].lower()
    doc_text = (doc_chunk.file_path + " " + doc_chunk.title + " " + doc_chunk.text).lower()
    if stem in doc_text or filename.lower() in doc_text:
        return True
    if stem in doc_chunk.file_path.lower():
        return True
    return False
