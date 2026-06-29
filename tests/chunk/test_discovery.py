"""Tests for doc file discovery."""

from scripts.chunk.config import GODOT_DOCS_DIR
from scripts.chunk.docs.discovery import discover_doc_files


def test_discover_includes_tutorials_and_classes():
    result = discover_doc_files(GODOT_DOCS_DIR)
    assert result.total_rst > 1000
    assert len(result.included) > 1000
    rels = {p.relative_to(GODOT_DOCS_DIR).as_posix() for p in result.included}
    assert "getting_started/first_2d_game/01.project_setup.rst" in rels
    assert "classes/class_node.rst" in rels


def test_discover_excludes_community():
    result = discover_doc_files(GODOT_DOCS_DIR)
    skipped_paths = {p.relative_to(GODOT_DOCS_DIR).as_posix() for p, _ in result.skipped}
    assert any(p.startswith("community/") for p in skipped_paths)
    assert any(p.startswith("about/") for p in skipped_paths)
