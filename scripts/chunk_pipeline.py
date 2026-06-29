#!/usr/bin/env python3
"""CLI for the Godot RAG chunking and ingestion pipeline."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.chunk.docs.pipeline import chunk_docs
from scripts.chunk.demos.pipeline import chunk_demos
from scripts.chunk.linking.pipeline import link_chunks
from scripts.chunk.merge import merge_and_write
from scripts.ingest.load_chroma import load_chunks_to_chroma
from scripts.ingest.query import query_chroma
from scripts.ingest.retriever import format_context_for_prompt, retrieve_for_agent
from scripts.eval.retrieval_eval import run_eval
from scripts.agent.godot_agent import ask
from scripts.agent.run_prompts import run_cases


def build_parser() -> argparse.ArgumentParser:
    """Build the pipeline argument parser (subcommands for each phase)."""
    parser = argparse.ArgumentParser(
        description="Godot RAG pipeline: chunk docs/demos, link, merge, ingest, query",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    docs_parser = sub.add_parser("chunk-docs", help="Chunk godot-docs RST files (Phase 1)")
    docs_parser.add_argument(
        "--no-semantic",
        action="store_true",
        help="Skip LangChain semantic splitting (faster iteration)",
    )
    docs_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSONL path (default: data/chunks_docs.jsonl)",
    )

    demos_parser = sub.add_parser("chunk-demos", help="Chunk godot-demo-projects (Phase 2)")
    demos_parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSONL path (default: data/chunks_demos.jsonl)",
    )

    sub.add_parser("link", help="Cross-link docs and demos (Phase 3)")
    sub.add_parser("merge", help="Merge doc + demo chunks (Phase 4)")

    all_parser = sub.add_parser("all", help="Run chunk-docs, chunk-demos, link, and merge")
    all_parser.add_argument(
        "--no-semantic",
        action="store_true",
        help="Skip LangChain semantic splitting for docs",
    )

    full_parser = sub.add_parser(
        "full",
        help="Run all + load-chroma (chunk, link, merge, Chroma ingest)",
    )
    full_parser.add_argument(
        "--no-semantic",
        action="store_true",
        help="Skip LangChain semantic splitting for docs",
    )
    full_parser.add_argument("--rebuild", action="store_true", help="Rebuild Chroma collection")
    full_parser.add_argument("--batch-size", type=int, default=100)
    full_parser.add_argument("--limit", type=int, default=None, help="Limit Chroma ingest to N chunks")

    chroma_parser = sub.add_parser("load-chroma", help="Load chunks.jsonl into ChromaDB (Phase 5)")
    chroma_parser.add_argument("--rebuild", action="store_true")
    chroma_parser.add_argument("--add", action="store_true", help="Use add instead of upsert")
    chroma_parser.add_argument("--batch-size", type=int, default=100)
    chroma_parser.add_argument("--limit", type=int, default=None)
    chroma_parser.add_argument("--chunks", type=str, default=None, help="Path to chunks.jsonl")
    chroma_parser.add_argument("--persist-dir", type=str, default=None, help="Chroma persist directory")

    query_parser = sub.add_parser("query", help="Query ChromaDB (Phase 5)")
    query_parser.add_argument("query_text", type=str)
    query_parser.add_argument("-n", "--num-results", type=int, default=5)
    query_parser.add_argument("--source-type", choices=["doc", "demo"], default=None)
    query_parser.add_argument(
        "--role",
        choices=["explanation", "api_ref", "code", "scene", "resource", "shader", "project_overview"],
        default=None,
    )
    query_parser.add_argument("--language", choices=["gdscript", "csharp", "cpp", "glsl"], default=None)
    query_parser.add_argument("--granularity", choices=["coarse", "fine"], default=None)
    query_parser.add_argument("--no-expand", action="store_true")
    query_parser.add_argument("--no-role-bias", action="store_true")
    query_parser.add_argument("--no-granularity-bias", action="store_true")
    query_parser.add_argument("--text-only", action="store_true")
    query_parser.add_argument("--persist-dir", type=str, default=None)

    retrieve_parser = sub.add_parser("retrieve", help="Agent retrieval with context slots (Phase 7)")
    retrieve_parser.add_argument("query_text", type=str)
    retrieve_parser.add_argument("--n-explanation", type=int, default=4)
    retrieve_parser.add_argument("--n-code", type=int, default=3)
    retrieve_parser.add_argument("--n-scene", type=int, default=2)
    retrieve_parser.add_argument("--include-scenes", action="store_true")
    retrieve_parser.add_argument("--no-scenes", action="store_true")
    retrieve_parser.add_argument("--prompt", action="store_true", help="Print formatted prompt context")
    retrieve_parser.add_argument("--persist-dir", type=str, default=None)

    eval_parser = sub.add_parser("eval-retrieval", help="Coarse vs fine retrieval eval (Phase 7)")
    eval_parser.add_argument("-n", "--num-results", type=int, default=5)
    eval_parser.add_argument("--persist-dir", type=str, default=None)
    eval_parser.add_argument("--output", type=str, default=None)

    ask_parser = sub.add_parser("ask", help="Ask the Godot RAG LangChain agent")
    ask_parser.add_argument("query_text", type=str)
    ask_parser.add_argument("--model", type=str, default=None)

    prompts_parser = sub.add_parser("agent-prompts", help="Run 3 targeted RAG agent prompt cases")
    prompts_parser.add_argument("--retrieval-only", action="store_true")
    prompts_parser.add_argument("--model", type=str, default=None)
    prompts_parser.add_argument("--output", type=str, default=None)

    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.command == "chunk-docs":
        result = chunk_docs(
            output_path=Path(args.output) if args.output else None,
            use_semantic=not args.no_semantic,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "chunk-demos":
        result = chunk_demos(
            output_path=Path(args.output) if args.output else None,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "link":
        result = link_chunks()
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "merge":
        result = merge_and_write()
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "all":
        chunk_docs(use_semantic=not args.no_semantic)
        chunk_demos()
        link_chunks()
        result = merge_and_write()
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "full":
        chunk_docs(use_semantic=not args.no_semantic)
        chunk_demos()
        link_chunks()
        merge_result = merge_and_write()
        chroma_result = load_chunks_to_chroma(
            rebuild=args.rebuild,
            batch_size=args.batch_size,
            limit=args.limit,
        )
        print(json.dumps({"merge": merge_result, "chroma": chroma_result}, indent=2))
        return 0

    if args.command == "load-chroma":
        result = load_chunks_to_chroma(
            chunks_path=Path(args.chunks) if args.chunks else None,
            persist_dir=Path(args.persist_dir) if args.persist_dir else None,
            rebuild=args.rebuild,
            upsert=not args.add,
            batch_size=args.batch_size,
            limit=args.limit,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "query":
        out = query_chroma(
            args.query_text,
            n_results=args.num_results,
            source_type=args.source_type,
            role=args.role,
            language=args.language,
            granularity=args.granularity,
            expand_links=not args.no_expand,
            role_bias=not args.no_role_bias,
            granularity_bias=not args.no_granularity_bias,
            persist_dir=Path(args.persist_dir) if args.persist_dir else None,
        )
        if args.text_only:
            for hit in out["results"] + out["expanded"]:
                print(f"--- {hit['chunk_id']} ---")
                print(hit["text"][:800])
                print()
        else:
            print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    if args.command == "retrieve":
        include_scenes = None
        if args.include_scenes:
            include_scenes = True
        elif args.no_scenes:
            include_scenes = False
        context = retrieve_for_agent(
            args.query_text,
            n_explanation=args.n_explanation,
            n_code=args.n_code,
            n_scene=args.n_scene,
            include_scenes=include_scenes,
            persist_dir=Path(args.persist_dir) if args.persist_dir else None,
        )
        if args.prompt:
            print(format_context_for_prompt(context))
        else:
            print(json.dumps(context.to_dict(), indent=2, ensure_ascii=False))
        return 0

    if args.command == "eval-retrieval":
        from scripts.chunk.config import DATA_DIR

        report = run_eval(
            persist_dir=Path(args.persist_dir) if args.persist_dir else None,
            n_results=args.num_results,
        )
        out_path = Path(args.output) if args.output else DATA_DIR / "retrieval_eval.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0

    if args.command == "ask":
        out = ask(args.query_text, model=args.model)
        print(out["answer"])
        return 0

    if args.command == "agent-prompts":
        report = run_cases(call_agent=not args.retrieval_only, model=args.model)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        if args.output:
            out_path = Path(args.output)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        return 0 if report["retrieval_all_passed"] else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
