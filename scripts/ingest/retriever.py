"""Agent-facing retriever: vector search, link expansion, context assembly."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.chunk.config import get_paths
from scripts.ingest.chroma_utils import (
    get_chroma_client,
    get_or_create_collection,
    parse_related_ids,
)
from scripts.ingest.query import infer_query_hints, query_chroma

EXPLANATION_ROLES = frozenset({"explanation", "api_ref"})
CODE_ROLES = frozenset({"code", "shader"})
SCENE_ROLES = frozenset({"scene", "resource"})

DODGE_PLAYER_RE = re.compile(r"dodge\s+the\s+creeps|first\s+2d\s+game", re.IGNORECASE)

ANCHOR_CHUNK_IDS: dict[str, list[str]] = {
    "dodge_player": [
        "doc:getting_started/first_2d_game/03.coding_the_player#coding_the_player:gdscript",
        "demo:2d/dodge_the_creeps/player.gd",
    ],
    "compute_heightmap": [
        "doc:tutorials/shaders/compute_shaders",
        "demo:compute/heightmap/main.gd:split_0",
    ],
}


def _fetch_anchor_chunks(collection, keys: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    doc_hits: list[dict[str, Any]] = []
    code_hits: list[dict[str, Any]] = []
    ids: list[str] = []
    for key in keys:
        ids.extend(ANCHOR_CHUNK_IDS.get(key, []))
    if not ids:
        return doc_hits, code_hits
    fetched = collection.get(ids=ids, include=["documents", "metadatas"])
    for i, cid in enumerate(fetched["ids"]):
        item = {
            "chunk_id": cid,
            "text": fetched["documents"][i],
            "metadata": fetched["metadatas"][i],
            "distance": None,
            "expanded": True,
        }
        if cid.startswith("doc:"):
            doc_hits.append(item)
        else:
            code_hits.append(item)
    return doc_hits, code_hits


def _anchor_keys_for_query(query: str) -> list[str]:
    keys: list[str] = []
    if DODGE_PLAYER_RE.search(query) and re.search(r"player", query, re.IGNORECASE):
        keys.append("dodge_player")
    if re.search(r"heightmap", query, re.IGNORECASE) and re.search(r"compute", query, re.IGNORECASE):
        keys.append("compute_heightmap")
    return keys


def _supplemental_queries(query: str) -> list[tuple[str, str]]:
    """Return (search_query, focus) pairs; focus is 'doc' or 'demo'."""
    extras: list[tuple[str, str]] = []
    if DODGE_PLAYER_RE.search(query) and re.search(r"player", query, re.IGNORECASE):
        extras.append(("getting_started first_2d_game coding the player", "doc"))
        extras.append(("2d/dodge_the_creeps/player.gd export speed Area2D", "demo"))
    if re.search(r"heightmap", query, re.IGNORECASE) and re.search(
        r"compute", query, re.IGNORECASE
    ):
        extras.append(("tutorials shaders compute_shaders heightmap demo", "doc"))
        extras.append(("compute/heightmap main.gd", "demo"))
    return extras


@dataclass
class AgentContext:
    """Structured retrieval result for a Godot expert agent."""

    query: str
    hints: dict[str, str | None]
    explanations: list[dict[str, Any]] = field(default_factory=list)
    code: list[dict[str, Any]] = field(default_factory=list)
    scenes: list[dict[str, Any]] = field(default_factory=list)
    linked: list[dict[str, Any]] = field(default_factory=list)

    def all_chunks(self) -> list[dict[str, Any]]:
        seen: set[str] = set()
        ordered: list[dict[str, Any]] = []
        for chunk in self.explanations + self.code + self.scenes + self.linked:
            cid = chunk["chunk_id"]
            if cid not in seen:
                seen.add(cid)
                ordered.append(chunk)
        return ordered

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "hints": self.hints,
            "explanations": self.explanations,
            "code": self.code,
            "scenes": self.scenes,
            "linked": self.linked,
        }


def _role_of(hit: dict[str, Any]) -> str:
    return hit.get("metadata", {}).get("role", "")


def _dedupe_hits(hits: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for hit in hits:
        cid = hit["chunk_id"]
        if cid in seen:
            continue
        seen.add(cid)
        out.append(hit)
        if len(out) >= limit:
            break
    return out


def _bucket_hits(
    hits: list[dict[str, Any]],
    *,
    explanations: list[dict[str, Any]],
    code: list[dict[str, Any]],
    scenes: list[dict[str, Any]],
    linked: list[dict[str, Any]],
) -> None:
    for hit in hits:
        role = _role_of(hit)
        if hit.get("expanded"):
            linked.append(hit)
        elif role in EXPLANATION_ROLES:
            explanations.append(hit)
        elif role in CODE_ROLES:
            code.append(hit)
        elif role in SCENE_ROLES:
            scenes.append(hit)
        elif hit.get("metadata", {}).get("source_type") == "demo":
            code.append(hit)
        else:
            explanations.append(hit)


def _boost_project_links(
    collection,
    hits: list[dict[str, Any]],
    explanations: list[dict[str, Any]],
    code: list[dict[str, Any]],
    *,
    max_docs: int = 2,
    max_code: int = 1,
) -> None:
    """Pull high-value tutorial/code links from demo project_overview chunks."""
    for hit in hits:
        if _role_of(hit) != "project_overview":
            continue
        related = parse_related_ids(hit.get("metadata", {}))
        if not related:
            continue
        related_blob = " ".join(related)
        if "coding_the_player" in related_blob:
            doc_filter = "coding_the_player"
            code_filter = "player.gd"
        elif "compute/heightmap" in hit.get("chunk_id", "") or "compute_shaders" in related_blob:
            doc_filter = "compute_shaders"
            code_filter = "heightmap"
        else:
            continue
        doc_ids = [rid for rid in related if rid.startswith("doc:") and doc_filter in rid][:max_docs]
        code_ids = [rid for rid in related if rid.startswith("demo:") and code_filter in rid][:max_code]
        fetch_ids = doc_ids + code_ids
        if not fetch_ids:
            continue
        fetched = collection.get(ids=fetch_ids, include=["documents", "metadatas"])
        for i, cid in enumerate(fetched["ids"]):
            item = {
                "chunk_id": cid,
                "text": fetched["documents"][i],
                "metadata": fetched["metadatas"][i],
                "distance": None,
                "expanded": True,
            }
            if cid.startswith("doc:"):
                explanations.append(item)
            else:
                code.append(item)


def retrieve_for_agent(
    query: str,
    *,
    n_explanation: int = 4,
    n_code: int = 3,
    n_scene: int = 2,
    include_scenes: bool | None = None,
    persist_dir: Path | None = None,
) -> AgentContext:
    """Retrieve docs + demos with separate context slots for an agent."""
    paths = get_paths()
    client = get_chroma_client(str(persist_dir or paths.chroma_persist))
    collection = get_or_create_collection(client, rebuild=False)

    hints = infer_query_hints(query)
    if include_scenes is None:
        include_scenes = hints.get("role") == "scene"

    explanations: list[dict[str, Any]] = []
    code: list[dict[str, Any]] = []
    scenes: list[dict[str, Any]] = []
    linked: list[dict[str, Any]] = []

    primary = query_chroma(
        query,
        n_results=max(n_explanation + n_code, 8),
        expand_links=True,
        role_bias=True,
        granularity_bias=True,
        persist_dir=persist_dir,
    )
    _bucket_hits(
        primary["results"] + primary["expanded"],
        explanations=explanations,
        code=code,
        scenes=scenes,
        linked=linked,
    )

    if len(explanations) < n_explanation:
        doc_hits = query_chroma(
            query,
            n_results=n_explanation,
            source_type="doc",
            role_bias=False,
            granularity_bias=True,
            expand_links=False,
            persist_dir=persist_dir,
        )
        _bucket_hits(
            doc_hits["results"],
            explanations=explanations,
            code=code,
            scenes=scenes,
            linked=linked,
        )

    if len(code) < n_code:
        demo_hits = query_chroma(
            query,
            n_results=n_code,
            source_type="demo",
            role="code",
            role_bias=False,
            granularity_bias=False,
            expand_links=False,
            persist_dir=persist_dir,
        )
        _bucket_hits(
            demo_hits["results"],
            explanations=explanations,
            code=code,
            scenes=scenes,
            linked=linked,
        )

    if include_scenes and len(scenes) < n_scene:
        scene_hits = query_chroma(
            query,
            n_results=n_scene,
            source_type="demo",
            role="scene",
            role_bias=False,
            granularity_bias=False,
            expand_links=False,
            persist_dir=persist_dir,
        )
        _bucket_hits(
            scene_hits["results"],
            explanations=explanations,
            code=code,
            scenes=scenes,
            linked=linked,
        )

    priority_explanations: list[dict[str, Any]] = []
    priority_code: list[dict[str, Any]] = []
    for extra_query, focus in _supplemental_queries(query):
        if focus == "doc":
            doc_extra = query_chroma(
                extra_query,
                n_results=n_explanation,
                source_type="doc",
                role_bias=False,
                granularity_bias=False,
                expand_links=True,
                persist_dir=persist_dir,
            )
            priority_explanations.extend(doc_extra["results"])
            _bucket_hits(
                doc_extra["expanded"],
                explanations=explanations,
                code=code,
                scenes=scenes,
                linked=linked,
            )
        else:
            demo_extra = query_chroma(
                extra_query,
                n_results=n_code,
                source_type="demo",
                role="code",
                role_bias=False,
                granularity_bias=False,
                expand_links=True,
                persist_dir=persist_dir,
            )
            priority_code.extend(demo_extra["results"])
            _bucket_hits(
                demo_extra["expanded"],
                explanations=explanations,
                code=code,
                scenes=scenes,
                linked=linked,
            )

    _boost_project_links(
        collection,
        primary["results"] + primary["expanded"] + explanations + code + linked,
        priority_explanations,
        priority_code,
    )

    anchor_doc, anchor_code = _fetch_anchor_chunks(collection, _anchor_keys_for_query(query))
    priority_explanations = anchor_doc + priority_explanations
    priority_code = anchor_code + priority_code

    explanations = _dedupe_hits(priority_explanations + explanations, n_explanation)
    code = _dedupe_hits(priority_code + code, n_code)

    return AgentContext(
        query=query,
        hints=hints,
        explanations=explanations,
        code=code,
        scenes=_dedupe_hits(scenes, n_scene if include_scenes else 0),
        linked=_dedupe_hits(linked, 5),
    )


def format_context_for_prompt(
    context: AgentContext,
    *,
    max_chars_per_chunk: int = 2000,
) -> str:
    """Format retrieved chunks as labeled sections for an LLM prompt."""
    sections: list[str] = []

    def _append_block(title: str, chunks: list[dict[str, Any]]) -> None:
        if not chunks:
            return
        parts = [f"## {title}"]
        for hit in chunks:
            meta = hit.get("metadata", {})
            header = f"### {hit['chunk_id']}"
            if meta.get("title"):
                header += f" — {meta['title']}"
            if meta.get("file_path"):
                header += f" ({meta['file_path']})"
            text = hit.get("text", "")[:max_chars_per_chunk]
            parts.append(f"{header}\n{text}")
        sections.append("\n\n".join(parts))

    _append_block("Documentation", context.explanations)
    _append_block("Example code", context.code)
    _append_block("Scenes and resources", context.scenes)
    _append_block("Linked context", context.linked)

    if not sections:
        return f"(No relevant Godot documentation found for: {context.query})"

    return "\n\n---\n\n".join(sections)
