"""Tests for RST utilities."""

from pathlib import Path

from scripts.chunk.docs.rst_utils import (
    iter_content_blocks,
    map_tab_language,
    parse_sections,
    preprocess_rst,
)


FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_preprocess_strips_toctree_and_images():
    raw = """
.. toctree::
   :maxdepth: 1

   child_page

Title
=====

Hello world.

.. image:: img/example.webp

More text.
"""
    out = preprocess_rst(raw)
    assert "toctree" not in out
    assert "[image: img/example.webp]" in out
    assert "Hello world" in out


def test_parse_sections():
    raw = preprocess_rst((FIXTURES / "sample_tutorial.rst").read_text(encoding="utf-8"))
    sections = parse_sections(raw)
    titles = [s.title for s in sections]
    assert "Coding the player" in titles
    assert "Player movement" in titles


def test_tab_parsing_languages():
    raw = preprocess_rst((FIXTURES / "sample_tutorial.rst").read_text(encoding="utf-8"))
    sections = parse_sections(raw)
    coding = next(s for s in sections if s.title == "Coding the player")
    blocks = list(iter_content_blocks(coding.content))
    tab_blocks = [b for t, b in blocks if t == "tabs"]
    assert tab_blocks
    tabs = tab_blocks[0]
    languages = {t.language for t in tabs}
    assert "gdscript" in languages
    assert "csharp" in languages
    cpp_tab = next(t for t in tabs if t.language == "cpp")
    assert cpp_tab.is_stub


def test_map_tab_language():
    assert map_tab_language("GDScript", "gdscript") == "gdscript"
    assert map_tab_language("C#") == "csharp"
