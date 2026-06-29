"""Chunk a single demo project into retrieval units."""

from __future__ import annotations

from pathlib import Path

from scripts.chunk.config import GODOT_VERSION
from scripts.chunk.demos.discovery import DemoProject
from scripts.chunk.demos.files import DemoFile, iter_project_files
from scripts.chunk.demos.project_godot import summarize_project_godot
from scripts.chunk.demos.readme import normalize_readme
from scripts.chunk.demos.scene import build_scene_chunk_text
from scripts.chunk.demos.script import chunk_script_file
from scripts.chunk.schema import Chunk, Language, make_demo_chunk_id, make_demo_project_id


def chunk_demo_project(project: DemoProject) -> list[Chunk]:
    """Produce all chunks for one demo project."""
    project_id = make_demo_project_id(project.category, project.project_name)
    files = iter_project_files(project.root)
    chunks: list[Chunk] = []

    readme_file = next((f for f in files if f.path.name == "README.md"), None)
    godot_file = next((f for f in files if f.path.name == "project.godot"), None)

    if readme_file:
        raw = readme_file.path.read_text(encoding="utf-8")
        text = normalize_readme(raw, project.category, project.project_name)
        chunks.append(
            Chunk(
                chunk_id=project_id,
                text=text,
                source_type="demo",
                role="project_overview",
                godot_version=GODOT_VERSION,
                hierarchy=[project.category, project.project_name],
                parent_id=None,
                file_path=f"{project.rel_path}/README.md",
                title=project.project_name,
            )
        )
    elif godot_file:
        raw = godot_file.path.read_text(encoding="utf-8")
        text = summarize_project_godot(raw, project.category, project.project_name)
        chunks.append(
            Chunk(
                chunk_id=project_id,
                text=text,
                source_type="demo",
                role="project_overview",
                godot_version=GODOT_VERSION,
                hierarchy=[project.category, project.project_name],
                parent_id=None,
                file_path=f"{project.rel_path}/project.godot",
                title=project.project_name,
            )
        )

    if godot_file and readme_file:
        raw = godot_file.path.read_text(encoding="utf-8")
        text = summarize_project_godot(raw, project.category, project.project_name)
        chunks.append(
            Chunk(
                chunk_id=make_demo_chunk_id(
                    project.category,
                    project.project_name,
                    "project.godot",
                ),
                text=text,
                source_type="demo",
                role="project_overview",
                godot_version=GODOT_VERSION,
                hierarchy=[project.category, project.project_name, "project.godot"],
                parent_id=project_id,
                file_path=f"{project.rel_path}/project.godot",
                title="project.godot",
            )
        )

    for demo_file in files:
        if demo_file.path.name in ("README.md", "project.godot"):
            continue
        chunks.extend(_chunk_demo_file(project, demo_file, project_id))

    return chunks


def _chunk_demo_file(
    project: DemoProject,
    demo_file: DemoFile,
    project_id: str,
) -> list[Chunk]:
    raw = demo_file.path.read_text(encoding="utf-8")
    rel = demo_file.rel_path
    file_path = f"{project.rel_path}/{rel}"
    stem = Path(rel).stem

    if demo_file.role == "scene":
        text = build_scene_chunk_text(
            raw,
            rel_path=rel,
            project_rel=project.rel_path,
            kind="Scene",
        )
        return [
            Chunk(
                chunk_id=make_demo_chunk_id(project.category, project.project_name, rel),
                text=text,
                source_type="demo",
                role="scene",
                godot_version=GODOT_VERSION,
                hierarchy=[project.category, project.project_name, stem],
                parent_id=project_id,
                file_path=file_path,
                title=Path(rel).name,
            )
        ]

    if demo_file.role == "resource":
        text = build_scene_chunk_text(
            raw,
            rel_path=rel,
            project_rel=project.rel_path,
            kind="Resource",
        )
        return [
            Chunk(
                chunk_id=make_demo_chunk_id(project.category, project.project_name, rel),
                text=text,
                source_type="demo",
                role="resource",
                godot_version=GODOT_VERSION,
                hierarchy=[project.category, project.project_name, stem],
                parent_id=project_id,
                file_path=file_path,
                title=Path(rel).name,
            )
        ]

    if demo_file.role in ("code", "shader"):
        return chunk_script_file(
            project=project,
            rel_path=rel,
            raw=raw,
            role=demo_file.role,
            language=demo_file.language,  # type: ignore[arg-type]
            parent_id=project_id,
        )

    return []
