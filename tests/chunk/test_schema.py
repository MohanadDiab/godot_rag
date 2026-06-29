"""Tests for chunk schema and ID helpers."""

import json
import tempfile
from pathlib import Path

import pytest

from scripts.chunk.schema import (
    Chunk,
    make_demo_chunk_id,
    make_demo_project_id,
    make_doc_chunk_id,
    read_chunks_jsonl,
    slugify,
    validate_chunk,
    write_chunks_jsonl,
)


def test_slugify():
    assert slugify("Coding the player") == "coding_the_player"
    assert slugify("  ") == "untitled"


def test_make_doc_chunk_id():
    assert make_doc_chunk_id(
        "getting_started/first_2d_game/03.coding_the_player.rst",
        "Coding the player",
    ) == "doc:getting_started/first_2d_game/03.coding_the_player#coding_the_player"


def test_make_demo_chunk_id():
    assert make_demo_project_id("2d", "dodge_the_creeps") == "demo:2d/dodge_the_creeps"
    assert (
        make_demo_chunk_id("2d", "dodge_the_creeps", "player.gd")
        == "demo:2d/dodge_the_creeps/player.gd"
    )


def test_chunk_roundtrip_jsonl():
    chunk = Chunk(
        chunk_id="doc:classes/class_node#description",
        text="Base class for all scene objects.",
        source_type="doc",
        role="api_ref",
        granularity="coarse",
        godot_version="4.x",
        hierarchy=["classes", "Node"],
        parent_id="doc:classes/class_node",
        file_path="classes/class_node.rst",
        title="Description",
        related_ids=["demo:2d/dodge_the_creeps"],
    )
    restored = Chunk.from_jsonl_line(chunk.to_jsonl_line())
    assert restored.chunk_id == chunk.chunk_id
    assert restored.related_ids == chunk.related_ids
    assert restored.granularity == "coarse"


def test_validate_chunk_rejects_empty_text():
    chunk = Chunk(
        chunk_id="demo:2d/test",
        text="   ",
        source_type="demo",
        role="code",
        godot_version="4.x",
        hierarchy=["2d", "test"],
        file_path="2d/test/main.gd",
        title="main.gd",
        language="gdscript",
    )
    errors = validate_chunk(chunk)
    assert errors
    assert "text must not be empty" in errors[0]


def test_write_and_read_chunks_jsonl():
    chunks = [
        Chunk(
            chunk_id="demo:2d/dodge_the_creeps",
            text="Dodge the Creeps demo project.",
            source_type="demo",
            role="project_overview",
            godot_version="4.x",
            hierarchy=["2d", "dodge_the_creeps"],
            file_path="2d/dodge_the_creeps/README.md",
            title="dodge_the_creeps",
        ),
    ]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "chunks.jsonl"
        assert write_chunks_jsonl(chunks, path) == 1
        loaded = read_chunks_jsonl(path)
        assert len(loaded) == 1
        assert loaded[0].chunk_id == chunks[0].chunk_id


def test_chunk_to_dict_omits_empty_optionals():
    chunk = Chunk(
        chunk_id="doc:test",
        text="Hello",
        source_type="doc",
        role="explanation",
        godot_version="4.x",
        hierarchy=[],
        file_path="test.rst",
        title="Test",
    )
    data = chunk.to_dict()
    assert "granularity" not in data
    assert "language" not in data
    assert "parent_id" not in data
    assert "related_ids" not in data
