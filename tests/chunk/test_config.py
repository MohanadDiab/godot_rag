"""Tests for pipeline configuration."""

from pathlib import Path

from scripts.chunk.config import (
    DOC_INCLUDE_DIRS,
    GODOT_DEMOS_DIR,
    GODOT_DOCS_DIR,
    ROOT_DIR,
    ensure_data_dirs,
    get_paths,
)


def test_root_paths_exist():
    assert ROOT_DIR.is_dir()
    assert GODOT_DOCS_DIR.is_dir()
    assert GODOT_DEMOS_DIR.is_dir()


def test_doc_include_dirs():
    for name in DOC_INCLUDE_DIRS:
        assert (GODOT_DOCS_DIR / name).is_dir(), f"missing doc dir: {name}"


def test_get_paths():
    paths = get_paths()
    assert paths.root == ROOT_DIR
    assert paths.chunks_jsonl.name == "chunks.jsonl"
    assert paths.chroma_persist.name == "chroma"


def test_ensure_data_dirs():
    paths = get_paths()
    ensure_data_dirs()
    assert paths.data.is_dir()
    assert paths.chroma_persist.is_dir()
