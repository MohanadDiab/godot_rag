"""Tests for doc ↔ demo link extraction."""

from scripts.chunk.linking.extract import (
    build_link_graph,
    extract_links_from_docs,
    load_override_links,
)


def test_override_links_dodge_the_creeps():
    graph = load_override_links()
    demo_paths = {p for link in graph.links for p in link.demo_paths}
    assert "2d/dodge_the_creeps" in demo_paths
    assert "mono/dodge_the_creeps" in demo_paths


def test_extract_docs_finds_first_2d_game():
    graph = extract_links_from_docs()
    pairs = [(link.doc_prefixes, link.demo_paths) for link in graph.links]
    assert any(
        "getting_started/first_2d_game" in prefixes and "2d/dodge_the_creeps" in demos
        for prefixes, demos in pairs
    )


def test_build_link_graph_non_empty():
    graph = build_link_graph()
    assert len(graph.links) >= 2
