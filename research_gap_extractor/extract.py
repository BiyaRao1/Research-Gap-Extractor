"""Extract structured research-gap insights from a paper's abstract using an LLM.

Any provider can be plugged in via the `LLMClient` protocol below; a working
Anthropic (Claude) implementation is included. The prompt-building and
response-parsing logic is provider-agnostic and unit-tested without a live
API key.
"""

from __future__ import annotations

import json
import os
from typing import Optional, Protocol

from .models import ExtractedInsight, Paper

SYSTEM_PROMPT = (
    "You are a research assistant helping a prospective PhD student scope "
    "possible research directions. Given a paper's title and abstract, "
    "extract only what the abstract itself supports — do not invent "
    "results or claims the abstract does not make. "
    "Respond with a single JSON object with exactly these keys: "
    '"key_methods" (list of short strings), '
    '"stated_limitations" (list of short strings; empty list if the abstract '
    "states none), "
    '"possible_extensions" (list of 2-4 short, concrete follow-up research '
    "ideas a PhD applicant could propose, grounded in the abstract), "
    '"one_line_summary" (a single sentence, <25 words). '
    "Return ONLY the JSON object, no other text."
)


def build_user_prompt(paper: Paper) -> str:
    return f"Title: {paper.title}\n\nAbstract: {paper.abstract}"


class LLMClient(Protocol):
    """Minimal interface an LLM backend must satisfy."""

    def complete(self, system: str, user: str) -> str:
        """Return the raw text completion for the given system/user prompts."""
        ...


class AnthropicClient:
    """Thin wrapper around the Anthropic Python SDK.

    Requires `pip install anthropic` and an `ANTHROPIC_API_KEY` environment
    variable (or pass `api_key` explicitly).
    """

    def __init__(self, model: str = "claude-sonnet-4-5", api_key: Optional[str] = None):
        try:
            import anthropic  # type: ignore
        except ImportError as exc:  # pragma: no cover - exercised only w/o the dep
            raise RuntimeError(
                "The 'anthropic' package is required for AnthropicClient. "
                "Install it with: pip install anthropic"
            ) from exc

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError(
                "Set the ANTHROPIC_API_KEY environment variable, or pass "
                "api_key= explicitly, to use AnthropicClient."
            )
        self._client = anthropic.Anthropic(api_key=key)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )


def parse_model_output(raw: str, paper_title: str) -> ExtractedInsight:
    """Parse the model's JSON response into an ExtractedInsight.

    Tolerant of the model wrapping the JSON in a code fence, since that is a
    common failure mode even with an explicit "JSON only" instruction.
    """
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {exc}\nRaw output: {raw}") from exc

    return ExtractedInsight(
        paper_title=paper_title,
        key_methods=list(data.get("key_methods", [])),
        stated_limitations=list(data.get("stated_limitations", [])),
        possible_extensions=list(data.get("possible_extensions", [])),
        one_line_summary=str(data.get("one_line_summary", "")),
        raw_model_output=raw,
    )


def extract_insight(paper: Paper, client: LLMClient) -> ExtractedInsight:
    """Run the extraction prompt for a single paper against `client`."""
    if not paper.abstract:
        return ExtractedInsight(
            paper_title=paper.title,
            one_line_summary="(no abstract available to analyze)",
        )
    raw = client.complete(SYSTEM_PROMPT, build_user_prompt(paper))
    return parse_model_output(raw, paper.title)


def extract_insights(papers: list[Paper], client: LLMClient) -> list[ExtractedInsight]:
    """Run extraction for a list of papers, skipping ones without an abstract."""
    return [extract_insight(p, client) for p in papers]
