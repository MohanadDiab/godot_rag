"""Shared chunk schema for the Godot RAG pipeline."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

SourceType = Literal["doc", "demo"]
Role = Literal[
    "explanation",
    "api_ref",
    "code",
    "scene",
    "resource",
    "shader",
    "project_overview",
]
Granularity = Literal["coarse", "fine"]
Language = Literal["gdscript", "csharp", "cpp", "glsl"]


@dataclass
class Chunk:
    """A single retrievable unit for embedding and storage."""

    chunk_id: str
    text: str
    source_type: SourceType
    role: Role
    godot_version: str
    hierarchy: list[str]
    file_path: str
    title: str
    granularity: Granularity | None = None
    language: Language | None = None
    parent_id: str | None = None
    related_ids: list[str] = field(default_factory=list)
    link_types: dict[str, str] = field(default_factory=dict)  # related_id -> link_type
    status: str | None = None  # e.g. "stub" for incomplete C++ tabs

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        # Omit null optional fields from JSONL for cleaner output
        return {k: v for k, v in data.items() if v is not None and v != [] and v != {}}

    def to_jsonl_line(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Chunk:
        return cls(
            chunk_id=data["chunk_id"],
            text=data["text"],
            source_type=data["source_type"],
            role=data["role"],
            godot_version=data.get("godot_version", "4.x"),
            hierarchy=data.get("hierarchy", []),
            file_path=data["file_path"],
            title=data["title"],
            granularity=data.get("granularity"),
            language=data.get("language"),
            parent_id=data.get("parent_id"),
            related_ids=data.get("related_ids", []),
            link_types=data.get("link_types", {}),
            status=data.get("status"),
        )

    @classmethod
    def from_jsonl_line(cls, line: str) -> Chunk:
        return cls.from_dict(json.loads(line))


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str, max_length: int = 80) -> str:
    """Convert arbitrary text to a stable, URL-safe slug."""
    slug = _SLUG_RE.sub("_", value.strip().lower()).strip("_")
    if not slug:
        return "untitled"
    return slug[:max_length].rstrip("_")


def make_doc_chunk_id(
    file_path: str,
    section: str | None = None,
    *,
    suffix: str | None = None,
) -> str:
    """
    Build a stable doc chunk ID.

    Examples:
        doc:getting_started/first_2d_game/03.coding_the_player.rst
        doc:classes/class_node.rst#method_process
    """
    normalized = file_path.replace("\\", "/").lstrip("/")
    if normalized.endswith(".rst"):
        normalized = normalized[:-4]
    base = f"doc:{normalized}"
    if section:
        base = f"{base}#{slugify(section)}"
    if suffix:
        base = f"{base}:{slugify(suffix)}"
    return base


def make_demo_chunk_id(
    category: str,
    project_name: str,
    relative_file: str | None = None,
    *,
    suffix: str | None = None,
) -> str:
    """
    Build a stable demo chunk ID.

    Examples:
        demo:2d/dodge_the_creeps
        demo:2d/dodge_the_creeps/player.gd
    """
    base = f"demo:{category}/{project_name}"
    if relative_file:
        rel = relative_file.replace("\\", "/").lstrip("/")
        base = f"{base}/{rel}"
    if suffix:
        base = f"{base}:{slugify(suffix)}"
    return base


def make_demo_project_id(category: str, project_name: str) -> str:
    """Project-level ID (parent for demo children)."""
    return make_demo_chunk_id(category, project_name)


def validate_chunk(chunk: Chunk) -> list[str]:
    """Return a list of validation errors (empty if valid)."""
    errors: list[str] = []

    if not chunk.chunk_id:
        errors.append("chunk_id is required")
    if not chunk.text.strip():
        errors.append("text must not be empty")
    if chunk.source_type not in ("doc", "demo"):
        errors.append(f"invalid source_type: {chunk.source_type}")
    if chunk.granularity is not None and chunk.granularity not in ("coarse", "fine"):
        errors.append(f"invalid granularity: {chunk.granularity}")
    if chunk.language is not None and chunk.language not in (
        "gdscript",
        "csharp",
        "cpp",
        "glsl",
    ):
        errors.append(f"invalid language: {chunk.language}")

    return errors


def write_chunks_jsonl(chunks: list[Chunk], path: str | Any) -> int:
    """Write chunks to a JSONL file. Returns number of lines written."""
    from pathlib import Path

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            errors = validate_chunk(chunk)
            if errors:
                raise ValueError(f"Invalid chunk {chunk.chunk_id}: {', '.join(errors)}")
            f.write(chunk.to_jsonl_line() + "\n")
    return len(chunks)


def read_chunks_jsonl(path: str | Any) -> list[Chunk]:
    """Read chunks from a JSONL file."""
    from pathlib import Path

    chunks: list[Chunk] = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(Chunk.from_jsonl_line(line))
    return chunks
