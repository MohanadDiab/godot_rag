"""Script and shader file chunking for demo projects."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.chunk.config import (
    DEMO_SCRIPT_SEMANTIC_SPLIT_LINE_THRESHOLD,
    GODOT_VERSION,
)
from scripts.chunk.demos.discovery import DemoProject
from scripts.chunk.schema import Chunk, Language, Role, make_demo_chunk_id

_GD_SPLIT_RE = re.compile(
    r"(?=^(?:@tool\s+)?(?:static\s+)?func\s+\w+|^class_name\s+|^class\s+\w+)",
    re.MULTILINE,
)
_CS_SPLIT_RE = re.compile(
    r"(?=^(?:public|private|protected|internal).*(?:class|void|override))",
    re.MULTILINE,
)


def build_script_header(
    rel_path: str,
    project: DemoProject,
    language: str,
) -> str:
    return f"File: {rel_path} | Project: {project.rel_path} | Language: {language}"


def chunk_script_file(
    *,
    project: DemoProject,
    rel_path: str,
    raw: str,
    role: Role,
    language: Language | None,
    parent_id: str,
) -> list[Chunk]:
    """Chunk a script/shader file; split long files on function boundaries."""
    header = build_script_header(rel_path, project, language or role)
    line_count = raw.count("\n") + 1
    stem = Path(rel_path).stem
    hierarchy = [project.category, project.project_name, stem]
    base_id = make_demo_chunk_id(project.category, project.project_name, rel_path)

    if line_count < DEMO_SCRIPT_SEMANTIC_SPLIT_LINE_THRESHOLD:
        return [
            Chunk(
                chunk_id=base_id,
                text=f"{header}\n---\n{raw}",
                source_type="demo",
                role=role,
                language=language,
                godot_version=GODOT_VERSION,
                hierarchy=hierarchy,
                parent_id=parent_id,
                file_path=f"{project.rel_path}/{rel_path}",
                title=Path(rel_path).name,
            )
        ]

    parts = _split_source(raw, language)
    if len(parts) <= 1:
        return [
            Chunk(
                chunk_id=base_id,
                text=f"{header}\n---\n{raw}",
                source_type="demo",
                role=role,
                language=language,
                godot_version=GODOT_VERSION,
                hierarchy=hierarchy,
                parent_id=parent_id,
                file_path=f"{project.rel_path}/{rel_path}",
                title=Path(rel_path).name,
            )
        ]

    chunks: list[Chunk] = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        chunks.append(
            Chunk(
                chunk_id=f"{base_id}:part_{i}",
                text=f"{header}\n---\n{part}",
                source_type="demo",
                role=role,
                language=language,
                godot_version=GODOT_VERSION,
                hierarchy=hierarchy + [f"part_{i}"],
                parent_id=parent_id,
                file_path=f"{project.rel_path}/{rel_path}",
                title=f"{Path(rel_path).name} (part {i + 1})",
            )
        )
    return chunks


def _split_source(raw: str, language: Language | None) -> list[str]:
    if language == "csharp":
        parts = _CS_SPLIT_RE.split(raw)
    elif language in ("gdscript", None):
        parts = _GD_SPLIT_RE.split(raw)
    else:
        parts = re.split(r"\n{2,}", raw)

    preamble = parts[0].strip() if parts else ""
    chunks: list[str] = []
    if preamble:
        chunks.append(preamble)
    for part in parts[1:]:
        if part.strip():
            chunks.append(part.strip())
    return chunks if len(chunks) > 1 else [raw]
