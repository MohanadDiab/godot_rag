"""Discover Godot demo projects by project.godot marker."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.chunk.config import DEMO_EXCLUDE_DIR_NAMES, DEMO_PROJECT_MARKER, GODOT_DEMOS_DIR


@dataclass(frozen=True)
class DemoProject:
    category: str
    project_name: str
    root: Path
    rel_path: str  # e.g. 2d/dodge_the_creeps

    @property
    def project_id(self) -> str:
        return f"demo:{self.category}/{self.project_name}"


def discover_demo_projects(demos_dir: Path | None = None) -> list[DemoProject]:
    """Find all directories containing project.godot."""
    root = demos_dir or GODOT_DEMOS_DIR
    projects: list[DemoProject] = []

    for marker in sorted(root.rglob(DEMO_PROJECT_MARKER)):
        project_root = marker.parent
        rel = project_root.relative_to(root).as_posix()
        parts = rel.split("/")
        if any(p in DEMO_EXCLUDE_DIR_NAMES for p in parts):
            continue
        if parts[0].startswith("."):
            continue

        category = parts[0]
        project_name = parts[-1] if len(parts) > 1 else parts[0]
        projects.append(
            DemoProject(
                category=category,
                project_name=project_name,
                root=project_root,
                rel_path=rel,
            )
        )

    return projects
