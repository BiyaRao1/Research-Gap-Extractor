import json

from research_gap_extractor.models import ExtractedInsight, Paper
from research_gap_extractor.report import to_json, to_markdown


def _sample_paper():
    return Paper(
        title="Sample Paper",
        abstract="Sample abstract.",
        authors=["A. Author"],
        year=2023,
        url="https://example.com",
        source="arxiv",
    )


def test_to_json_without_insights():
    papers = [_sample_paper()]
    output = json.loads(to_json(papers))
    assert len(output) == 1
    assert output[0]["title"] == "Sample Paper"
    assert output[0]["insight"] is None


def test_to_json_with_insights():
    papers = [_sample_paper()]
    insights = [ExtractedInsight(paper_title="Sample Paper", one_line_summary="Short.")]
    output = json.loads(to_json(papers, insights))
    assert output[0]["insight"]["one_line_summary"] == "Short."


def test_to_markdown_includes_title_and_abstract():
    papers = [_sample_paper()]
    md = to_markdown(papers)
    assert "## Sample Paper" in md
    assert "Sample abstract." in md
    assert "A. Author" in md


def test_to_markdown_includes_insight_sections():
    papers = [_sample_paper()]
    insights = [
        ExtractedInsight(
            paper_title="Sample Paper",
            key_methods=["Method X"],
            stated_limitations=["Limitation Y"],
            possible_extensions=["Extension Z"],
            one_line_summary="A summary.",
        )
    ]
    md = to_markdown(papers, insights)
    assert "**Summary:** A summary." in md
    assert "Method X" in md
    assert "Limitation Y" in md
    assert "- Extension Z" in md
