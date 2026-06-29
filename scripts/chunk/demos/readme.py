"""Normalize demo README.md files for chunking."""

from __future__ import annotations

import re

from scripts.chunk.config import README_EXCLUDE_SECTIONS

_SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
_LANG_LINE_RE = re.compile(r"^\*?\*?Language[s]?:\*?\*?\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_RENDERER_LINE_RE = re.compile(r"^\*?\*?Renderer:\*?\*?\s*(.+)$", re.IGNORECASE | re.MULTILINE)


def normalize_readme(raw: str, category: str, project_name: str) -> str:
    """Strip low-value sections and prepend project header."""
    text = raw.replace("\r\n", "\n")
    text = _strip_sections(text, README_EXCLUDE_SECTIONS)
    text = _strip_image_blocks(text)
    text = text.strip()

    header = f"Project: {category}/{project_name}"
    if not text:
        return header
    return f"{header}\n\n{text}"


def _strip_sections(text: str, exclude: frozenset[str]) -> str:
    sections = _SECTION_RE.split(text)
    if len(sections) <= 1:
        return text

    kept = [sections[0].strip()]
    i = 1
    while i < len(sections):
        title = sections[i].strip().lower()
        body = sections[i + 1] if i + 1 < len(sections) else ""
        if title not in exclude:
            kept.append(f"## {sections[i].strip()}\n\n{body.strip()}")
        i += 2
    return "\n\n".join(part for part in kept if part.strip())


def _strip_image_blocks(text: str) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("![") and "](" in stripped:
            continue
        if stripped.startswith("> [!NOTE]") or stripped.startswith("> [!WARNING]"):
            lines.append(line)
            continue
        lines.append(line)
    return "\n".join(lines)
