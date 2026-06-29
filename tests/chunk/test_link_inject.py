"""Tests for link injection into chunks."""

from scripts.chunk.config import GODOT_DEMOS_DIR, GODOT_DOCS_DIR
from scripts.chunk.demos.discovery import discover_demo_projects
from scripts.chunk.demos.project import chunk_demo_project
from scripts.chunk.docs.tutorial import chunk_tutorial_file
from scripts.chunk.linking.extract import load_override_links
from scripts.chunk.linking.inject import inject_links
from scripts.chunk.linking.graph import LinkGraph


def test_inject_dodge_the_creeps_links():
    doc_path = GODOT_DOCS_DIR / "getting_started/first_2d_game/03.coding_the_player.rst"
    doc_chunks = chunk_tutorial_file(
        "getting_started/first_2d_game/03.coding_the_player.rst",
        doc_path.read_text(encoding="utf-8"),
    )
    project = next(p for p in discover_demo_projects(GODOT_DEMOS_DIR) if p.rel_path == "2d/dodge_the_creeps")
    demo_chunks = chunk_demo_project(project)

    graph = LinkGraph()
    for link in load_override_links().links:
        graph.add(link)

    linked = inject_links(doc_chunks + demo_chunks, graph)
    doc_linked = [c for c in linked if c.source_type == "doc"]
    demo_linked = [c for c in linked if c.source_type == "demo"]

    assert any(c.related_ids for c in doc_linked)
    assert any(c.related_ids for c in demo_linked)

    player_doc = next(c for c in doc_linked if "coding_the_player" in c.chunk_id)
    assert any("dodge_the_creeps" in rid for rid in player_doc.related_ids)

    player_demo = next(c for c in demo_linked if c.title == "player.gd")
    assert any("coding_the_player" in rid for rid in player_demo.related_ids)
    assert player_demo.link_types
