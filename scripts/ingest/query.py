"""Query ChromaDB with optional filters and link expansion."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.chunk.config import get_paths
from scripts.ingest.chroma_utils import (
    get_chroma_client,
    get_or_create_collection,
    parse_related_ids,
)

CODE_QUERY_RE = re.compile(
    r"\b(?:\.gd|\.cs|script|implement|code|func |player\.gd)\b",
    re.IGNORECASE,
)
SCENE_QUERY_RE = re.compile(
    r"\b(?:\.tscn|scene|signal connection|\[connection\b)\b",
    re.IGNORECASE,
)
EXPLAIN_QUERY_RE = re.compile(
    r"\b(?:how|what|why|explain|tutorial|documentation|work\?)\b",
    re.IGNORECASE,
)
API_CLASS_RE = re.compile(
    r"\b[A-Z][a-zA-Z0-9]*(?:2D|3D|UI|XR|API)?[A-Z][a-zA-Z0-9]*\b",
)
METHOD_RE = re.compile(
    r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b",
)


def infer_role_bias(query: str) -> str | None:
    """Return preferred role based on simple query heuristics."""
    if SCENE_QUERY_RE.search(query):
        return "scene"
    if CODE_QUERY_RE.search(query):
        return "code"
    if EXPLAIN_QUERY_RE.search(query):
        return "explanation"
    if API_CLASS_RE.search(query):
        return "api_ref"
    return None


def infer_granularity_bias(query: str) -> str | None:
    """Prefer fine chunks for method-level queries, coarse for class overviews."""
    if METHOD_RE.search(query):
        return "fine"
    if EXPLAIN_QUERY_RE.search(query) and API_CLASS_RE.search(query):
        return "coarse"
    return None


def infer_query_hints(query: str) -> dict[str, str | None]:
    """Heuristic filters for agent retrieval."""
    return {
        "role": infer_role_bias(query),
        "granularity": infer_granularity_bias(query),
    }


def build_where_filter(
    *,
    source_type: str | None = None,
    role: str | None = None,
    language: str | None = None,
    granularity: str | None = None,
) -> dict[str, Any] | None:
    clauses: list[dict[str, Any]] = []
    if source_type:
        clauses.append({"source_type": source_type})
    if role:
        clauses.append({"role": role})
    if language:
        clauses.append({"language": language})
    if granularity:
        clauses.append({"granularity": granularity})

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def expand_related(
    collection,
    hits: list[dict[str, Any]],
    *,
    max_related: int = 5,
) -> list[dict[str, Any]]:
    """Fetch linked chunks for top hits."""
    related_ids: list[str] = []
    seen = {h["chunk_id"] for h in hits}

    for hit in hits:
        for rid in parse_related_ids(hit.get("metadata", {})):
            if rid not in seen:
                related_ids.append(rid)
                seen.add(rid)
            if len(related_ids) >= max_related:
                break
        if len(related_ids) >= max_related:
            break

    if not related_ids:
        return []

    fetched = collection.get(ids=related_ids, include=["documents", "metadatas"])
    expanded: list[dict[str, Any]] = []
    for i, cid in enumerate(fetched["ids"]):
        expanded.append(
            {
                "chunk_id": cid,
                "text": fetched["documents"][i],
                "metadata": fetched["metadatas"][i],
                "distance": None,
                "expanded": True,
            }
        )
    return expanded


def query_chroma(
    query: str,
    *,
    n_results: int = 5,
    source_type: str | None = None,
    role: str | None = None,
    language: str | None = None,
    granularity: str | None = None,
    expand_links: bool = True,
    role_bias: bool = True,
    granularity_bias: bool = True,
    persist_dir: Path | None = None,
) -> dict[str, Any]:
    paths = get_paths()
    client = get_chroma_client(str(persist_dir or paths.chroma_persist))
    collection = get_or_create_collection(client, rebuild=False)

    if role_bias and role is None:
        role = infer_role_bias(query)
    if granularity_bias and granularity is None:
        granularity = infer_granularity_bias(query)

    where = build_where_filter(
        source_type=source_type,
        role=role,
        language=language,
        granularity=granularity,
    )

    kwargs: dict[str, Any] = {
        "query_texts": [query],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    if not results["ids"][0] and where and (role or granularity):
        relaxed = {k: v for k, v in kwargs.items() if k != "where"}
        if source_type or language:
            relaxed["where"] = build_where_filter(
                source_type=source_type,
                language=language,
            )
        results = collection.query(**relaxed)

    if not results["ids"][0] and where and role:
        relaxed = {k: v for k, v in kwargs.items() if k != "where"}
        if source_type or language or granularity:
            relaxed["where"] = build_where_filter(
                source_type=source_type,
                language=language,
                granularity=granularity,
            )
        results = collection.query(**relaxed)

    if not results["ids"][0] and where:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

    hits: list[dict[str, Any]] = []
    for i, cid in enumerate(results["ids"][0]):
        hits.append(
            {
                "chunk_id": cid,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results["distances"] else None,
                "expanded": False,
            }
        )

    expanded = expand_related(collection, hits) if expand_links else []

    return {
        "query": query,
        "filters": {
            "source_type": source_type,
            "role": role,
            "language": language,
            "granularity": granularity,
        },
        "results": hits,
        "expanded": expanded,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query the Godot RAG Chroma collection")
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument("-n", "--num-results", type=int, default=5)
    parser.add_argument("--source-type", choices=["doc", "demo"], default=None)
    parser.add_argument(
        "--role",
        choices=["explanation", "api_ref", "code", "scene", "resource", "shader", "project_overview"],
        default=None,
    )
    parser.add_argument("--language", choices=["gdscript", "csharp", "cpp", "glsl"], default=None)
    parser.add_argument("--granularity", choices=["coarse", "fine"], default=None)
    parser.add_argument("--no-expand", action="store_true", help="Skip related_ids expansion")
    parser.add_argument("--no-role-bias", action="store_true")
    parser.add_argument("--no-granularity-bias", action="store_true")
    parser.add_argument("--persist-dir", type=str, default=None)
    parser.add_argument("--text-only", action="store_true", help="Print chunk text snippets only")
    args = parser.parse_args(argv)

    out = query_chroma(
        args.query,
        n_results=args.num_results,
        source_type=args.source_type,
        role=args.role,
        language=args.language,
        granularity=args.granularity,
        expand_links=not args.no_expand,
        role_bias=not args.no_role_bias,
        granularity_bias=not args.no_granularity_bias,
        persist_dir=Path(args.persist_dir) if args.persist_dir else None,
    )

    if args.text_only:
        for hit in out["results"] + out["expanded"]:
            print(f"--- {hit['chunk_id']} ---")
            print(hit["text"][:800])
            print()
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
