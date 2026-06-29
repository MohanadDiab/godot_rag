"""Tests for corpus merge and integrity validation."""

import json
import tempfile
from pathlib import Path

import pytest

from scripts.chunk.config import CHUNKS_DEMOS_JSONL_PATH, CHUNKS_DOCS_JSONL_PATH
from scripts.chunk.merge import merge_and_write, merge_chunks, repair_chunks, validate_integrity
from scripts.chunk.schema import Chunk, read_chunks_jsonl, write_chunks_jsonl


def _sample_doc() -> Chunk:
    return Chunk(
        chunk_id="doc:test/page",
        text="Doc content",
        source_type="doc",
        role="explanation",
        godot_version="4.x",
        hierarchy=["test"],
        file_path="test/page.rst",
        title="Page",
    )


def _sample_demo_child() -> Chunk:
    return Chunk(
        chunk_id="demo:2d/foo/main.gd",
        text="extends Node",
        source_type="demo",
        role="code",
        godot_version="4.x",
        hierarchy=["2d", "foo", "main"],
        parent_id="demo:2d/foo",
        file_path="2d/foo/main.gd",
        title="main.gd",
        language="gdscript",
    )


def _sample_demo_overview() -> Chunk:
    return Chunk(
        chunk_id="demo:2d/foo",
        text="Foo demo",
        source_type="demo",
        role="project_overview",
        godot_version="4.x",
        hierarchy=["2d", "foo"],
        parent_id=None,
        file_path="2d/foo/README.md",
        title="foo",
    )


def test_merge_chunks_rejects_cross_source_duplicates():
    doc = _sample_doc()
    with pytest.raises(ValueError, match="Cross-source"):
        merge_chunks([doc], [doc])


def test_deduplicate_within_source():
    doc = _sample_doc()
    merged, meta = merge_chunks([doc, doc], [])
    assert len(merged) == 1
    assert meta["doc_duplicates_removed"] == 1


def test_repair_chunks_nulls_missing_parent():
    child = _sample_demo_child()
    repaired, stats = repair_chunks([child])
    assert stats["parent_nulled"] == 1
    assert repaired[0].parent_id is None


def test_validate_integrity_ok():
    chunks = [_sample_doc(), _sample_demo_overview(), _sample_demo_child()]
    report = validate_integrity(chunks, strict=False)
    assert report.ok


def test_merge_and_write_integration():
    if not CHUNKS_DOCS_JSONL_PATH.exists() or not CHUNKS_DEMOS_JSONL_PATH.exists():
        pytest.skip("Requires chunks_docs.jsonl and chunks_demos.jsonl")

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "chunks.jsonl"
        stats = Path(tmp) / "corpus_stats.json"
        result = merge_and_write(
            docs_jsonl=CHUNKS_DOCS_JSONL_PATH,
            demos_jsonl=CHUNKS_DEMOS_JSONL_PATH,
            output_jsonl=out,
            stats_path=stats,
        )
        assert result["merged_chunks"] == result["written"]
        assert result["integrity"]["ok"]
        assert out.exists()
        loaded = read_chunks_jsonl(out)
        assert len(loaded) == result["written"]
        stats_data = json.loads(stats.read_text(encoding="utf-8"))
        assert stats_data["total_chunks"] == result["written"]
