"""Tests for the unified pipeline CLI."""

import pytest

from scripts.chunk_pipeline import build_parser


@pytest.mark.parametrize(
    "command",
    [
        "chunk-docs",
        "chunk-demos",
        "link",
        "merge",
        "all",
        "full",
        "load-chroma",
        "query",
        "retrieve",
        "eval-retrieval",
        "ask",
        "agent-prompts",
    ],
)
def test_parser_registers_subcommands(command):
    parser = build_parser()
    extra: list[str] = []
    if command in ("query", "retrieve", "ask"):
        extra = ["test query"]
    args = parser.parse_args([command] + extra)
    assert args.command == command


def test_main_unknown_command_returns_error():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args([])
    assert exc.value.code != 0


def test_main_help_does_not_crash(capsys):
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--help"])
