"""User-facing CLI for the Godot RAG agent."""

from __future__ import annotations

import argparse
import sys


def _configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def ask_main(argv: list[str] | None = None) -> int:
    """Entry point for ``godot-ask`` — ask the Godot RAG agent."""
    from godot_rag import GodotAgent, search

    _configure_stdout()
    parser = argparse.ArgumentParser(
        prog="godot-ask",
        description="Ask the Godot RAG agent about Godot 4.x docs and demos.",
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Question to ask (omit for interactive mode)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="OpenAI model name (default: OPENAI_MODEL env or gpt-5-nano)",
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Retrieve context without calling OpenAI",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Interactive Q&A session (type 'exit' or Ctrl+C to quit)",
    )
    args = parser.parse_args(argv)

    if args.search_only:
        if not args.question:
            parser.error("question is required with --search-only")
        print(search(args.question))
        return 0

    agent = GodotAgent(model=args.model)

    if args.interactive or not args.question:
        print("Godot RAG — interactive mode (type 'exit' to quit)\n")
        while True:
            try:
                question = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if not question:
                continue
            if question.lower() in {"exit", "quit", "q"}:
                return 0
            print(f"\nAgent: {agent.ask(question)}\n")
        return 0

    print(agent.ask(args.question))
    return 0
