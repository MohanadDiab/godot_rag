"""Retrieval quality evaluation: coarse vs fine vs unfiltered."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.chunk.config import DATA_DIR
from scripts.ingest.query import query_chroma

EVAL_QUERIES: list[dict[str, Any]] = [
    {
        "query": "CharacterBody2D move_and_slide",
        "category": "api_method",
        "expect_any": ["move_and_slide", "characterbody2d", "character_body"],
    },
    {
        "query": "How does CharacterBody2D move_and_slide work?",
        "category": "api_explain",
        "expect_any": ["move_and_slide", "character_body", "characterbody2d"],
    },
    {
        "query": "What is CharacterBody2D",
        "category": "api_overview",
        "expect_any": ["characterbody2d", "character_body"],
    },
    {
        "query": "dodge the creeps player.gd movement",
        "category": "demo_code",
        "expect_any": ["dodge_the_creeps", "player.gd", "coding_the_player"],
    },
    {
        "query": "fix signal connection in tscn",
        "category": "scene",
        "expect_any": ["connection", ".tscn", "signal"],
    },
    {
        "query": "compute shader heightmap",
        "category": "demo_project",
        "expect_any": ["heightmap", "compute"],
    },
    {
        "query": "OpenXR action map",
        "category": "resource_doc",
        "expect_any": ["openxr", "action_map", "actionmap"],
    },
]

MODES = ("unfiltered", "coarse", "fine")


@dataclass
class EvalHit:
    chunk_id: str
    distance: float | None
    role: str
    matched: bool


def _matches_expectation(chunk_id: str, text: str, expect_any: list[str]) -> bool:
    blob = f"{chunk_id} {text}".lower()
    return any(token.lower() in blob for token in expect_any)


def _score_query(
    query: str,
    expect_any: list[str],
    *,
    granularity: str | None,
    n_results: int = 5,
    persist_dir: Path | None = None,
) -> dict[str, Any]:
    out = query_chroma(
        query,
        n_results=n_results,
        granularity=granularity,
        role_bias=False,
        granularity_bias=False,
        expand_links=False,
        persist_dir=persist_dir,
    )
    hits: list[EvalHit] = []
    for hit in out["results"]:
        matched = _matches_expectation(hit["chunk_id"], hit.get("text", ""), expect_any)
        hits.append(
            EvalHit(
                chunk_id=hit["chunk_id"],
                distance=hit.get("distance"),
                role=hit.get("metadata", {}).get("role", ""),
                matched=matched,
            )
        )
    top_match = hits[0].matched if hits else False
    any_match = any(h.matched for h in hits)
    return {
        "granularity": granularity or "unfiltered",
        "top_match": top_match,
        "any_match_in_top_n": any_match,
        "hits": [
            {
                "chunk_id": h.chunk_id,
                "distance": h.distance,
                "role": h.role,
                "matched": h.matched,
            }
            for h in hits
        ],
    }


def run_eval(
    *,
    persist_dir: Path | None = None,
    n_results: int = 5,
) -> dict[str, Any]:
    """Run coarse vs fine vs unfiltered eval across predefined queries."""
    by_category: dict[str, dict[str, int]] = {}
    results: list[dict[str, Any]] = []

    for item in EVAL_QUERIES:
        category = item["category"]
        by_category.setdefault(category, {m: 0 for m in MODES})
        mode_results: dict[str, Any] = {}
        for mode in MODES:
            granularity = None if mode == "unfiltered" else mode
            scored = _score_query(
                item["query"],
                item["expect_any"],
                granularity=granularity,
                n_results=n_results,
                persist_dir=persist_dir,
            )
            mode_results[mode] = scored
            if scored["top_match"]:
                by_category[category][mode] += 1

        winner = max(
            MODES,
            key=lambda m: (
                mode_results[m]["top_match"],
                mode_results[m]["any_match_in_top_n"],
            ),
        )
        results.append(
            {
                "query": item["query"],
                "category": category,
                "expect_any": item["expect_any"],
                "modes": mode_results,
                "recommended_mode": winner,
            }
        )

    category_winners: dict[str, str] = {}
    for category, scores in by_category.items():
        category_winners[category] = max(MODES, key=lambda m: scores[m])

    return {
        "n_results": n_results,
        "queries": results,
        "category_top1_scores": by_category,
        "category_recommended_mode": category_winners,
        "overall_recommended": {
            "api_method": "fine",
            "api_explain": "unfiltered",
            "api_overview": "coarse",
            "demo_code": "unfiltered",
            "scene": "unfiltered",
            "demo_project": "unfiltered",
            "resource_doc": "unfiltered",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate retrieval: coarse vs fine vs unfiltered")
    parser.add_argument("-n", "--num-results", type=int, default=5)
    parser.add_argument("--persist-dir", type=str, default=None)
    parser.add_argument(
        "--output",
        type=str,
        default=str(DATA_DIR / "retrieval_eval.json"),
        help="Write JSON results to this path",
    )
    args = parser.parse_args(argv)

    report = run_eval(
        persist_dir=Path(args.persist_dir) if args.persist_dir else None,
        n_results=args.num_results,
    )
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
