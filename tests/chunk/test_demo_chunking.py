"""Tests for demo file filtering and chunking."""

from pathlib import Path

from scripts.chunk.config import GODOT_DEMOS_DIR
from scripts.chunk.demos.discovery import discover_demo_projects
from scripts.chunk.demos.files import classify_file, iter_project_files
from scripts.chunk.demos.project import chunk_demo_project
from scripts.chunk.demos.readme import normalize_readme
from scripts.chunk.demos.scene import build_scene_chunk_text, parse_scene_root

GODOT_DEMOS = GODOT_DEMOS_DIR


def test_classify_excludes_import_and_uid():
    root = GODOT_DEMOS / "2d" / "dodge_the_creeps"
    assert classify_file(root / "main.gd.uid", root) is None
    assert classify_file(root / "art" / "playerGrey_walk1.png.import", root) is None


def test_classify_includes_gd_and_tscn():
    root = GODOT_DEMOS / "2d" / "dodge_the_creeps"
    gd = classify_file(root / "main.gd", root)
    tscn = classify_file(root / "main.tscn", root)
    assert gd and gd.role == "code" and gd.language == "gdscript"
    assert tscn and tscn.role == "scene"


def test_readme_strips_copying_section():
    raw = (GODOT_DEMOS / "2d" / "dodge_the_creeps" / "README.md").read_text(encoding="utf-8")
    out = normalize_readme(raw, "2d", "dodge_the_creeps")
    assert "Project: 2d/dodge_the_creeps" in out
    assert "Copying" not in out
    assert "Screenshots" not in out


def test_tscn_full_content_preserved():
    root = GODOT_DEMOS / "2d" / "dodge_the_creeps"
    raw = (root / "player.tscn").read_text(encoding="utf-8")
    text = build_scene_chunk_text(raw, rel_path="player.tscn", project_rel="2d/dodge_the_creeps")
    assert "---" in text
    assert "[connection signal=" in text
    assert "AnimatedSprite2D" in text
    name, typ = parse_scene_root(raw)
    assert name == "Player"
    assert typ == "Area2D"


def test_chunk_dodge_the_creeps():
    project = next(p for p in discover_demo_projects(GODOT_DEMOS) if p.rel_path == "2d/dodge_the_creeps")
    chunks = chunk_demo_project(project)
    roles = {c.role for c in chunks}
    assert "project_overview" in roles
    assert "code" in roles
    assert "scene" in roles
    assert not any(c.file_path.endswith(".uid") for c in chunks)
    assert not any(c.file_path.endswith(".import") for c in chunks)
    player = next(c for c in chunks if c.title == "player.tscn")
    assert "[connection signal=" in player.text


def test_chunk_long_script_splits_on_functions():
    project = next(
        p
        for p in discover_demo_projects(GODOT_DEMOS)
        if p.rel_path == "2d/physics_tests"
    )
    chunks = chunk_demo_project(project)
    long_chunks = [
        c for c in chunks if "test_one_way_collision.gd" in c.file_path
    ]
    assert len(long_chunks) >= 2


def test_chunk_mono_dodge_the_creeps():
    project = next(p for p in discover_demo_projects(GODOT_DEMOS) if p.rel_path == "mono/dodge_the_creeps")
    chunks = chunk_demo_project(project)
    csharp = [c for c in chunks if c.language == "csharp"]
    assert csharp
