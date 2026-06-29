"""Tests for agent retriever and query heuristics."""

from scripts.ingest.query import (
    infer_granularity_bias,
    infer_query_hints,
    infer_role_bias,
)
from scripts.ingest.retriever import AgentContext, format_context_for_prompt


def test_infer_role_bias_scene():
    assert infer_role_bias("fix signal connection in tscn") == "scene"


def test_infer_role_bias_explanation():
    assert infer_role_bias("How does move_and_slide work?") == "explanation"


def test_infer_granularity_bias_method():
    assert infer_granularity_bias("CharacterBody2D move_and_slide") == "fine"


def test_infer_granularity_bias_overview():
    assert infer_granularity_bias("How does CharacterBody2D work?") == "coarse"


def test_infer_query_hints():
    hints = infer_query_hints("fix signal connection in player.tscn")
    assert hints["role"] == "scene"


def test_format_context_for_prompt():
    context = AgentContext(
        query="test",
        hints={"role": "code", "granularity": None},
        explanations=[
            {
                "chunk_id": "doc:test/page",
                "text": "Use move_and_slide for kinematic bodies.",
                "metadata": {"title": "Movement", "file_path": "tutorials/move.rst"},
            }
        ],
        code=[
            {
                "chunk_id": "demo:2d/foo/player.gd",
                "text": "extends CharacterBody2D",
                "metadata": {"title": "player.gd", "file_path": "2d/foo/player.gd"},
            }
        ],
    )
    prompt = format_context_for_prompt(context)
    assert "## Documentation" in prompt
    assert "## Example code" in prompt
    assert "move_and_slide" in prompt
    assert "player.gd" in prompt


def test_format_context_empty():
    context = AgentContext(query="nothing here", hints={})
    assert "No relevant Godot documentation" in format_context_for_prompt(context)
