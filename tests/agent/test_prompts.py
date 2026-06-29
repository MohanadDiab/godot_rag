"""Tests for targeted RAG prompt cases (retrieval scoring only)."""

import pytest

from scripts.agent.prompts import RAG_PROMPT_CASES
from scripts.agent.run_prompts import score_retrieval


def test_three_prompt_cases_defined():
    assert len(RAG_PROMPT_CASES) == 3
    ids = {c.id for c in RAG_PROMPT_CASES}
    assert ids == {
        "character_body_move_and_slide",
        "compute_shader_heightmap",
        "first_2d_game_player",
    }


@pytest.mark.integration
def test_retrieval_scores_for_all_cases():
    for case in RAG_PROMPT_CASES:
        result = score_retrieval(case)
        assert result["token_hits"], f"{case.id}: no token hits in {result['chunk_ids']}"
        assert result["passed"], f"{case.id} failed: {result}"
