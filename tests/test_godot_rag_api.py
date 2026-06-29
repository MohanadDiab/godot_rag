"""Tests for the public godot_rag package API."""

from unittest.mock import MagicMock, patch

from godot_rag import GodotAgent, ask, search


def test_search_returns_formatted_string():
    with patch("godot_rag.retrieve_for_agent") as mock_retrieve:
        from scripts.ingest.retriever import AgentContext

        mock_retrieve.return_value = AgentContext(query="test", hints={})
        with patch("godot_rag.format_context_for_prompt", return_value="formatted"):
            assert search("test query") == "formatted"


def test_ask_returns_answer_dict():
    with patch("scripts.agent.godot_agent.build_agent") as mock_build:
        from langchain_core.messages import AIMessage

        mock_agent = MagicMock()
        mock_agent.invoke.return_value = {
            "messages": [AIMessage(content="Test answer")],
        }
        mock_build.return_value = mock_agent

        result = ask("What is Node2D?")
        assert result["question"] == "What is Node2D?"
        assert result["answer"] == "Test answer"


def test_godot_agent_ask():
    with patch("scripts.agent.godot_agent.ask", return_value={"answer": "hi"}):
        agent = GodotAgent(model="gpt-test")
        assert agent.ask("hello") == "hi"
