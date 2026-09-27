import json

import pytest

from research_gap_extractor.extract import (
    build_user_prompt,
    extract_insight,
    parse_model_output,
)
from research_gap_extractor.models import Paper


class FakeLLMClient:
    """A stand-in for AnthropicClient that returns a canned response."""

    def __init__(self, response: str):
        self._response = response
        self.last_system = None
        self.last_user = None

    def complete(self, system: str, user: str) -> str:
        self.last_system = system
        self.last_user = user
        return self._response


def test_build_user_prompt_includes_title_and_abstract():
    paper = Paper(title="My Title", abstract="My abstract text.")
    prompt = build_user_prompt(paper)
    assert "My Title" in prompt
    assert "My abstract text." in prompt


def test_parse_model_output_plain_json():
    raw = json.dumps(
        {
            "key_methods": ["Method A"],
            "stated_limitations": ["Small dataset"],
            "possible_extensions": ["Try on a second language pair"],
            "one_line_summary": "A short summary.",
        }
    )
    insight = parse_model_output(raw, paper_title="Some Paper")
    assert insight.paper_title == "Some Paper"
    assert insight.key_methods == ["Method A"]
    assert insight.stated_limitations == ["Small dataset"]
    assert insight.possible_extensions == ["Try on a second language pair"]
    assert insight.one_line_summary == "A short summary."


def test_parse_model_output_strips_code_fence():
    raw = "```json\n" + json.dumps({"one_line_summary": "Fenced."}) + "\n```"
    insight = parse_model_output(raw, paper_title="Fenced Paper")
    assert insight.one_line_summary == "Fenced."


def test_parse_model_output_invalid_json_raises():
    with pytest.raises(ValueError):
        parse_model_output("not json at all", paper_title="Broken Paper")


def test_extract_insight_calls_client_and_parses_result():
    raw = json.dumps(
        {
            "key_methods": ["Z3 solving"],
            "stated_limitations": [],
            "possible_extensions": ["Scale to larger models"],
            "one_line_summary": "Uses Z3 to generate test data.",
        }
    )
    client = FakeLLMClient(raw)
    paper = Paper(title="Test Data Gen", abstract="We use Z3 to generate test data.")

    insight = extract_insight(paper, client)

    assert insight.paper_title == "Test Data Gen"
    assert insight.key_methods == ["Z3 solving"]
    assert "Z3" in client.last_user


def test_extract_insight_skips_papers_without_abstract():
    client = FakeLLMClient("{}")
    paper = Paper(title="No Abstract", abstract="")

    insight = extract_insight(paper, client)

    assert insight.one_line_summary == "(no abstract available to analyze)"
    assert client.last_user is None  # client should never have been called
