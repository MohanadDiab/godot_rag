"""Extract doc ↔ demo links from source files and overrides."""

from __future__ import annotations

import json
import re
from pathlib import Path

from scripts.chunk.config import (
    DOC_INCLUDE_DIRS,
    GODOT_DEMOS_DIR,
    GODOT_DOCS_DIR,
    LINK_OVERRIDES_PATH,
)
from scripts.chunk.linking.graph import LinkGraph, ProjectLink

DEMO_GITHUB_RE = re.compile(
    r"github\.com/godotengine/godot-demo-projects/tree/[^/\s\)`>\"]+/([^\s\)`>\"]+)",
    re.IGNORECASE,
)
DOC_URL_RE = re.compile(
    r"docs\.godotengine\.org/en/(?:latest|stable)/([a-z0-9_./-]+?)(?:\.html|/index\.html)?",
    re.IGNORECASE,
)
DOC_PATH_IN_RST_RE = re.compile(
    r":doc:`([^`]+)`",
)


def _normalize_doc_path(path: str) -> str:
    path = path.strip().strip("/")
    if path.endswith("/index"):
        path = path[: -len("/index")]
    if path.endswith(".rst"):
        path = path[: -4]
    return path


def _normalize_demo_path(path: str) -> str:
    return path.strip().strip("/").replace("\\", "/")


def load_override_links(path: Path | None = None) -> LinkGraph:
    graph = LinkGraph()
    overrides_path = path or LINK_OVERRIDES_PATH
    if not overrides_path.exists():
        return graph

    data = json.loads(overrides_path.read_text(encoding="utf-8"))
    for _key, entry in data.items():
        demo_paths = entry.get("demo_paths") or [entry["demo_path"]]
        doc_paths = [_normalize_doc_path(p) for p in entry.get("doc_paths", [])]
        graph.add(
            ProjectLink(
                doc_prefixes=doc_paths,
                demo_paths=[_normalize_demo_path(p) for p in demo_paths],
                link_type="tutorial_to_demo",
                source="override",
            )
        )
    return graph


def extract_links_from_docs(docs_dir: Path | None = None) -> LinkGraph:
    """Scan RST files for GitHub demo project URLs."""
    root = docs_dir or GODOT_DOCS_DIR
    graph = LinkGraph()
    pairs: dict[str, set[str]] = {}

    for include_dir in DOC_INCLUDE_DIRS:
        base = root / include_dir
        if not base.exists():
            continue
        for rst_path in base.rglob("*.rst"):
            rel_doc = rst_path.relative_to(root).as_posix()
            if "/" in rel_doc:
                doc_prefix = _normalize_doc_path("/".join(rel_doc.split("/")[:-1]))
            else:
                doc_prefix = _normalize_doc_path(rel_doc)

            text = rst_path.read_text(encoding="utf-8")
            for match in DEMO_GITHUB_RE.finditer(text):
                demo_path = _normalize_demo_path(match.group(1))
                pairs.setdefault(doc_prefix, set()).add(demo_path)

    for doc_prefix, demo_paths in pairs.items():
        graph.add(
            ProjectLink(
                doc_prefixes=[doc_prefix],
                demo_paths=sorted(demo_paths),
                link_type="tutorial_to_demo",
                source="doc_url",
            )
        )
    return graph


def extract_links_from_demos(demos_dir: Path | None = None) -> LinkGraph:
    """Scan README.md and project.godot for documentation URLs."""
    root = demos_dir or GODOT_DEMOS_DIR
    graph = LinkGraph()

    for marker in root.rglob("project.godot"):
        project_root = marker.parent
        demo_path = project_root.relative_to(root).as_posix()
        doc_prefixes: set[str] = set()

        readme = project_root / "README.md"
        if readme.exists():
            doc_prefixes |= _extract_doc_prefixes_from_text(readme.read_text(encoding="utf-8"))

        godot_text = marker.read_text(encoding="utf-8")
        doc_prefixes |= _extract_doc_prefixes_from_text(godot_text)

        if doc_prefixes:
            graph.add(
                ProjectLink(
                    doc_prefixes=sorted(doc_prefixes),
                    demo_paths=[demo_path],
                    link_type="demo_to_tutorial",
                    source="demo_url",
                )
            )

    return graph


def _extract_doc_prefixes_from_text(text: str) -> set[str]:
    prefixes: set[str] = set()
    for match in DOC_URL_RE.finditer(text):
        prefixes.add(_normalize_doc_path(match.group(1)))
    for match in DOC_PATH_IN_RST_RE.finditer(text):
        prefixes.add(_normalize_doc_path(match.group(1)))
    return prefixes


def extract_heuristic_name_links(demos_dir: Path | None = None) -> LinkGraph:
    """Match demo folder names that appear in documentation directory paths."""
    root = demos_dir or GODOT_DEMOS_DIR
    docs_root = GODOT_DOCS_DIR
    graph = LinkGraph()

    doc_files: list[Path] = []
    for include_dir in DOC_INCLUDE_DIRS:
        base = docs_root / include_dir
        if base.exists():
            doc_files.extend(base.rglob("*.rst"))

    for marker in root.rglob("project.godot"):
        demo_path = marker.parent.relative_to(root).as_posix()
        project_name = demo_path.split("/")[-1]

        for rst_path in doc_files:
            rel = rst_path.relative_to(docs_root).as_posix()
            if project_name not in rel:
                continue
            doc_prefix = _normalize_doc_path("/".join(rel.split("/")[:-1]))
            graph.add(
                ProjectLink(
                    doc_prefixes=[doc_prefix],
                    demo_paths=[demo_path],
                    link_type="tutorial_to_demo",
                    source="heuristic",
                )
            )
    return graph


def build_link_graph(
    *,
    docs_dir: Path | None = None,
    demos_dir: Path | None = None,
    overrides_path: Path | None = None,
) -> LinkGraph:
    """Combine all link extraction strategies."""
    graph = LinkGraph()
    graph.merge(load_override_links(overrides_path))
    graph.merge(extract_links_from_docs(docs_dir))
    graph.merge(extract_links_from_demos(demos_dir))
    graph.merge(extract_heuristic_name_links(demos_dir))
    return consolidate_graph(graph)


def consolidate_graph(graph: LinkGraph) -> LinkGraph:
    """Merge links that share doc prefixes or demo paths."""
    merged: dict[tuple[tuple[str, ...], tuple[str, ...]], ProjectLink] = {}
    for link in graph.links:
        key = (tuple(sorted(link.doc_prefixes)), tuple(sorted(link.demo_paths)))
        if key in merged:
            continue
        merged[key] = link
    return LinkGraph(links=list(merged.values()))
