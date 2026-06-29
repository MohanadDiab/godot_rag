"""Discover and filter RST files in godot-docs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from scripts.chunk.config import DOC_EXCLUDE_DIRS, DOC_INCLUDE_DIRS, GODOT_DOCS_DIR


@dataclass
class DiscoveryResult:
    included: list[Path] = field(default_factory=list)
    skipped: list[tuple[Path, str]] = field(default_factory=list)

    @property
    def total_rst(self) -> int:
        return len(self.included) + len(self.skipped)


def _is_under_excluded_dir(path: Path, docs_root: Path) -> str | None:
    rel = path.relative_to(docs_root)
    for part in rel.parts:
        if part in DOC_EXCLUDE_DIRS:
            return f"excluded directory: {part}"
    return None


def _is_included_top_level(path: Path, docs_root: Path) -> bool:
    rel = path.relative_to(docs_root)
    if not rel.parts:
        return False
    top = rel.parts[0]
    return top in DOC_INCLUDE_DIRS


def discover_doc_files(docs_dir: Path | None = None) -> DiscoveryResult:
    """Walk godot-docs and return included/skipped RST files."""
    root = docs_dir or GODOT_DOCS_DIR
    result = DiscoveryResult()

    for path in sorted(root.rglob("*.rst")):
        reason = _is_under_excluded_dir(path, root)
        if reason:
            result.skipped.append((path, reason))
            continue
        if not _is_included_top_level(path, root):
            result.skipped.append((path, "outside include dirs"))
            continue
        result.included.append(path)

    return result
