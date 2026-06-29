"""Scene (.tscn) and resource (.tres) file chunking."""

from __future__ import annotations

import re
from pathlib import Path

_NODE_RE = re.compile(
    r'^\[node name="([^"]+)" type="([^"]+)"(?: parent="([^"]*)")?',
    re.MULTILINE,
)


def build_scene_chunk_text(
    raw: str,
    *,
    rel_path: str,
    project_rel: str,
    kind: str = "Scene",
) -> str:
    """Prepend retrieval header and include full file content."""
    filename = Path(rel_path).name
    res_path = f"res://{rel_path.replace(chr(92), '/')}"
    root_name, root_type = parse_scene_root(raw)
    header = (
        f"{kind}: {res_path} | Root: {root_type} ({root_name}) | "
        f"File: {project_rel}/{rel_path}"
    )
    return f"{header}\n---\n{raw}"


def parse_scene_root(text: str) -> tuple[str, str]:
    """Return (node_name, node_type) for the scene root."""
    for match in _NODE_RE.finditer(text):
        name, node_type, parent = match.group(1), match.group(2), match.group(3)
        if parent is None or parent == "" or parent == ".":
            return name, node_type
    return "unknown", "unknown"
