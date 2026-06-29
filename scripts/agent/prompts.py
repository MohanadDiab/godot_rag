"""Targeted prompts for validating Godot RAG retrieval."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RagPromptCase:
    """A prompt with known ground-truth sources in the corpus."""

    id: str
    prompt: str
    description: str
    expect_any: tuple[str, ...]
    expect_doc_paths: tuple[str, ...] = ()
    expect_demo_paths: tuple[str, ...] = ()


RAG_PROMPT_CASES: tuple[RagPromptCase, ...] = (
    RagPromptCase(
        id="character_body_move_and_slide",
        prompt=(
            "In Godot 4, how should I move a CharacterBody2D each physics frame? "
            "Should I set position directly, or use a specific method?"
        ),
        description="Physics tutorial: move_and_slide vs setting position",
        expect_any=("move_and_slide", "using_character_body_2d", "characterbody2d"),
        expect_doc_paths=("tutorials/physics/using_character_body_2d.rst",),
    ),
    RagPromptCase(
        id="compute_shader_heightmap",
        prompt=(
            "Where can I find an example of generating a heightmap with a compute shader in Godot 4, "
            "and what demo project demonstrates it?"
        ),
        description="Compute shaders doc + compute/heightmap demo",
        expect_any=("compute/heightmap", "heightmap", "compute_shader"),
        expect_doc_paths=("tutorials/shaders/compute_shaders.rst",),
        expect_demo_paths=("compute/heightmap",),
    ),
    RagPromptCase(
        id="first_2d_game_player",
        prompt=(
            "I'm following the first 2D game tutorial. How is the player movement implemented "
            "in the dodge the creeps demo?"
        ),
        description="first_2d_game tutorial linked to dodge_the_creeps player.gd",
        expect_any=(
            "coding_the_player",
            "dodge_the_creeps",
            "player.gd",
            "first_2d_game",
        ),
        expect_doc_paths=("getting_started/first_2d_game/03.coding_the_player.rst",),
        expect_demo_paths=("2d/dodge_the_creeps/player.gd", "2d/dodge_the_creeps"),
    ),
)
