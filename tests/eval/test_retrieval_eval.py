"""Tests for retrieval eval scoring helpers."""

from scripts.eval.retrieval_eval import EVAL_QUERIES, _matches_expectation


def test_matches_expectation():
    assert _matches_expectation("doc:classes/class_characterbody2d#move_and_slide:fine", "", ["move_and_slide"])
    assert not _matches_expectation("doc:other", "unrelated", ["move_and_slide"])


def test_eval_queries_defined():
    assert len(EVAL_QUERIES) >= 5
    for item in EVAL_QUERIES:
        assert item["query"]
        assert item["category"]
        assert item["expect_any"]


def test_run_eval_structure():
    """Smoke test eval report shape without requiring Chroma (mock-free unit check)."""
    # run_eval needs chroma - only test import and query list here
    categories = {q["category"] for q in EVAL_QUERIES}
    assert "api_method" in categories
    assert "scene" in categories
