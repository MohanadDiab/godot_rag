"""Tests for demo project discovery."""

from scripts.chunk.config import GODOT_DEMOS_DIR
from scripts.chunk.demos.discovery import discover_demo_projects


def test_discover_demo_projects_count():
    projects = discover_demo_projects(GODOT_DEMOS_DIR)
    assert len(projects) >= 130


def test_discover_dodge_the_creeps():
    projects = discover_demo_projects(GODOT_DEMOS_DIR)
    ids = {p.rel_path for p in projects}
    assert "2d/dodge_the_creeps" in ids
    assert "mono/dodge_the_creeps" in ids
    assert "compute/heightmap" in ids
