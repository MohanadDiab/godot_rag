"""Integration test: load a small JSONL corpus into Chroma and query it."""

import gc
import tempfile
from pathlib import Path

import pytest

from scripts.chunk.schema import Chunk, write_chunks_jsonl
from scripts.ingest.load_chroma import load_chunks_to_chroma
from scripts.ingest.query import query_chroma


def _release_chroma_client() -> None:
    """Release Chroma file handles so temp dirs can be removed on Windows."""
    try:
        from chromadb.api.client import SharedSystemClient

        SharedSystemClient.clear_system_cache()
    except Exception:
        pass
    gc.collect()


@pytest.fixture
def sample_chunks() -> list[Chunk]:
    return [
        Chunk(
            chunk_id="doc:tutorials/physics/character_body#move_and_slide",
            text="CharacterBody2D.move_and_slide() moves the body and slides along collisions.",
            source_type="doc",
            role="explanation",
            godot_version="4.x",
            hierarchy=["tutorials", "physics", "character_body"],
            file_path="tutorials/physics/character_body.rst",
            title="move_and_slide",
        ),
        Chunk(
            chunk_id="demo:2d/navigation/character.gd",
            text="extends CharacterBody2D\n\nfunc _physics_process(delta):\n    move_and_slide()",
            source_type="demo",
            role="code",
            godot_version="4.x",
            hierarchy=["2d", "navigation", "character.gd"],
            file_path="2d/navigation/character.gd",
            title="character.gd",
            language="gdscript",
            related_ids=["doc:tutorials/physics/character_body#move_and_slide"],
            link_types={"doc:tutorials/physics/character_body#move_and_slide": "demo_to_tutorial"},
        ),
    ]


@pytest.mark.integration
def test_load_and_query_roundtrip(sample_chunks):
    tmp = tempfile.mkdtemp()
    tmp_path = Path(tmp)
    jsonl_path = tmp_path / "chunks.jsonl"
    chroma_dir = tmp_path / "chroma"
    try:
        write_chunks_jsonl(sample_chunks, jsonl_path)

        ingest = load_chunks_to_chroma(
            chunks_path=jsonl_path,
            persist_dir=chroma_dir,
            rebuild=True,
        )
        assert ingest["chunks_ingested"] == 2

        out = query_chroma(
            "How does move_and_slide work?",
            n_results=2,
            persist_dir=chroma_dir,
            expand_links=True,
            role_bias=False,
        )
        assert out["results"]
        assert any("move_and_slide" in hit["text"] for hit in out["results"])
        if out["expanded"]:
            assert any(hit.get("expanded") for hit in out["expanded"])
    finally:
        _release_chroma_client()
        import shutil

        shutil.rmtree(tmp, ignore_errors=True)
