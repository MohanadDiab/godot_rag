"""Tests for tutorial and class reference chunking."""

from pathlib import Path

from scripts.chunk.docs.class_ref import chunk_class_ref_file
from scripts.chunk.docs.tutorial import chunk_tutorial_file

GODOT_DOCS = Path(__file__).resolve().parents[2] / "godot-docs"
FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_chunk_tutorial_tabs():
    raw = (FIXTURES / "sample_tutorial.rst").read_text(encoding="utf-8")
    chunks = chunk_tutorial_file("getting_started/test/sample.rst", raw)
    assert chunks
    languages = {c.language for c in chunks if c.language}
    assert "gdscript" in languages
    assert "csharp" in languages
    assert "cpp" not in languages  # stub excluded


def test_chunk_real_tutorial_file():
    path = GODOT_DOCS / "getting_started/first_2d_game/03.coding_the_player.rst"
    chunks = chunk_tutorial_file(
        "getting_started/first_2d_game/03.coding_the_player.rst",
        path.read_text(encoding="utf-8"),
    )
    assert len(chunks) >= 5
    langs = {c.language for c in chunks if c.language}
    assert "gdscript" in langs
    assert "csharp" in langs


def test_chunk_class_ref_coarse_and_fine():
    path = GODOT_DOCS / "classes/class_characterbody2d.rst"
    chunks = chunk_class_ref_file(
        "classes/class_characterbody2d.rst",
        path.read_text(encoding="utf-8"),
    )
    coarse = [c for c in chunks if c.granularity == "coarse"]
    fine = [c for c in chunks if c.granularity == "fine"]
    assert coarse
    assert fine
    assert any("Properties" in c.title for c in coarse)
    assert any("move_and_slide" in c.chunk_id or "move_and_slide" in c.text for c in fine)


def test_chunk_class_node_has_many_fine_methods():
    path = GODOT_DOCS / "classes/class_node.rst"
    chunks = chunk_class_ref_file(
        "classes/class_node.rst",
        path.read_text(encoding="utf-8"),
    )
    fine = [c for c in chunks if c.granularity == "fine"]
    assert len(fine) > 50


def test_tutorial_parent_id_hierarchy():
    raw = (FIXTURES / "sample_tutorial.rst").read_text(encoding="utf-8")
    chunks = chunk_tutorial_file("getting_started/test/sample.rst", raw)
    file_id = "doc:getting_started/test/sample"
    file_chunk = next(c for c in chunks if c.chunk_id == file_id)
    assert file_chunk.parent_id is None

    coding_section = next(c for c in chunks if c.chunk_id.endswith("#coding_the_player"))
    assert coding_section.parent_id == file_id

    gdscript_tab = next(c for c in chunks if c.language == "gdscript")
    assert gdscript_tab.parent_id == coding_section.chunk_id

    movement = next(c for c in chunks if c.title == "Player movement")
    assert movement.parent_id == file_id


def test_chunk_id_stability():
    raw = (FIXTURES / "sample_tutorial.rst").read_text(encoding="utf-8")
    rel = "getting_started/test/sample.rst"
    first = chunk_tutorial_file(rel, raw)
    second = chunk_tutorial_file(rel, raw)
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]

    path = GODOT_DOCS / "classes/class_characterbody2d.rst"
    content = path.read_text(encoding="utf-8")
    a = chunk_class_ref_file("classes/class_characterbody2d.rst", content)
    b = chunk_class_ref_file("classes/class_characterbody2d.rst", content)
    assert [c.chunk_id for c in a] == [c.chunk_id for c in b]
