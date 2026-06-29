"""Tests for Chroma metadata serialization and query helpers."""

import json

from scripts.chunk.schema import Chunk
from scripts.ingest.chroma_utils import chunk_to_chroma_metadata, parse_related_ids
from scripts.ingest.query import build_where_filter, infer_granularity_bias, infer_role_bias


def test_chunk_to_chroma_metadata():
    chunk = Chunk(
        chunk_id="demo:2d/foo/main.gd",
        text="extends Node",
        source_type="demo",
        role="code",
        godot_version="4.x",
        hierarchy=["2d", "foo", "main"],
        file_path="2d/foo/main.gd",
        title="main.gd",
        language="gdscript",
        related_ids=["doc:test/page"],
        link_types={"doc:test/page": "demo_to_tutorial"},
    )
    meta = chunk_to_chroma_metadata(chunk)
    assert meta["source_type"] == "demo"
    assert meta["language"] == "gdscript"
    assert json.loads(meta["related_ids"]) == ["doc:test/page"]
    assert json.loads(meta["link_types"]) == {"doc:test/page": "demo_to_tutorial"}


def test_parse_related_ids():
    meta = {"related_ids": '["a", "b"]'}
    assert parse_related_ids(meta) == ["a", "b"]


def test_build_where_filter():
    assert build_where_filter(source_type="doc") == {"source_type": "doc"}
    combined = build_where_filter(source_type="demo", role="code")
    assert combined == {"$and": [{"source_type": "demo"}, {"role": "code"}]}


def test_infer_role_bias():
    assert infer_role_bias("fix signal connection in tscn") == "scene"
    assert infer_role_bias("How does move_and_slide work?") == "explanation"


def test_infer_granularity_bias():
    assert infer_granularity_bias("move_and_slide") == "fine"
