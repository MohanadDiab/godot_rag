"""Run targeted RAG prompt cases and check retrieval + agent answers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.agent.godot_agent import ask
from scripts.agent.prompts import RAG_PROMPT_CASES, RagPromptCase
from scripts.ingest.retriever import retrieve_for_agent


def _blob_from_context(context) -> str:
    parts: list[str] = []
    for hit in context.all_chunks():
        parts.append(hit.get("chunk_id", ""))
        parts.append(hit.get("text", ""))
        meta = hit.get("metadata", {})
        parts.append(str(meta.get("file_path", "")))
    return "\n".join(parts).lower()


def score_retrieval(case: RagPromptCase) -> dict[str, Any]:
    context = retrieve_for_agent(case.prompt)
    blob = _blob_from_context(context)

    token_hits = [t for t in case.expect_any if t.lower() in blob]
    doc_hits = [p for p in case.expect_doc_paths if p.lower() in blob]
    demo_hits = [p for p in case.expect_demo_paths if p.lower() in blob]

    passed = bool(token_hits) and (
        not case.expect_doc_paths or bool(doc_hits)
    ) and (
        not case.expect_demo_paths or bool(demo_hits)
    )

    return {
        "passed": passed,
        "token_hits": token_hits,
        "doc_path_hits": doc_hits,
        "demo_path_hits": demo_hits,
        "chunk_ids": [c["chunk_id"] for c in context.all_chunks()],
        "hints": context.hints,
    }


def run_cases(*, call_agent: bool = True, model: str | None = None) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for case in RAG_PROMPT_CASES:
        retrieval = score_retrieval(case)
        entry: dict[str, Any] = {
            "id": case.id,
            "description": case.description,
            "prompt": case.prompt,
            "retrieval": retrieval,
        }
        if call_agent:
            agent_out = ask(case.prompt, model=model)
            entry["answer"] = agent_out["answer"]
            answer_blob = agent_out["answer"].lower()
            entry["answer_mentions_expected"] = any(
                token.lower() in answer_blob for token in case.expect_any
            )
        results.append(entry)

    retrieval_passed = sum(1 for r in results if r["retrieval"]["passed"])
    return {
        "total": len(results),
        "retrieval_passed": retrieval_passed,
        "retrieval_all_passed": retrieval_passed == len(results),
        "cases": results,
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Run 3 targeted Godot RAG prompt cases")
    parser.add_argument("--retrieval-only", action="store_true", help="Skip OpenAI agent calls")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args(argv)

    report = run_cases(call_agent=not args.retrieval_only, model=args.model)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")

    return 0 if report["retrieval_all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
