"""Filter and classify files within a demo project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.chunk.config import (
    DEMO_EXCLUDE_ASSET_SUFFIXES,
    DEMO_EXCLUDE_DIR_NAMES,
    DEMO_EXCLUDE_FILE_NAMES,
    DEMO_EXCLUDE_FILE_SUFFIXES,
    DEMO_INCLUDE_CODE_SUFFIXES,
    DEMO_INCLUDE_DOC_SUFFIXES,
    DEMO_INCLUDE_RESOURCE_SUFFIXES,
    DEMO_INCLUDE_SCENE_SUFFIXES,
    DEMO_INCLUDE_SHADER_SUFFIXES,
)
from scripts.chunk.schema import Role


@dataclass(frozen=True)
class DemoFile:
    path: Path
    rel_path: str
    role: Role
    language: str | None = None


_SKIP_DIR_NAMES = DEMO_EXCLUDE_DIR_NAMES | {"assets"}


def should_skip_path(path: Path, project_root: Path) -> bool:
    rel = path.relative_to(project_root)
    for part in rel.parts:
        if part in _SKIP_DIR_NAMES:
            return True
    return False


def classify_file(path: Path, project_root: Path) -> DemoFile | None:
    if not path.is_file():
        return None
    if should_skip_path(path, project_root):
        return None

    name = path.name
    suffix = path.suffix.lower()

    if name in DEMO_EXCLUDE_FILE_NAMES:
        return None
    if suffix in DEMO_EXCLUDE_FILE_SUFFIXES:
        return None
    if suffix in DEMO_EXCLUDE_ASSET_SUFFIXES:
        return None

    rel_path = path.relative_to(project_root).as_posix()

    if name == "README.md":
        return DemoFile(path, rel_path, "project_overview")
    if name == "project.godot":
        return DemoFile(path, rel_path, "project_overview")

    if suffix in DEMO_INCLUDE_CODE_SUFFIXES:
        lang = "gdscript" if suffix == ".gd" else "csharp"
        return DemoFile(path, rel_path, "code", lang)
    if suffix in DEMO_INCLUDE_SHADER_SUFFIXES:
        lang = "glsl" if suffix == ".glsl" else None
        role: Role = "shader"
        return DemoFile(path, rel_path, role, lang)
    if suffix in DEMO_INCLUDE_SCENE_SUFFIXES:
        return DemoFile(path, rel_path, "scene")
    if suffix in DEMO_INCLUDE_RESOURCE_SUFFIXES:
        return DemoFile(path, rel_path, "resource")

    if suffix in DEMO_INCLUDE_DOC_SUFFIXES and name != "README.md":
        return None

    return None


def iter_project_files(project_root: Path) -> list[DemoFile]:
    files: list[DemoFile] = []
    for path in sorted(project_root.rglob("*")):
        demo_file = classify_file(path, project_root)
        if demo_file:
            files.append(demo_file)
    return files
