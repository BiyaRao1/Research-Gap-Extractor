from pathlib import Path

from research_gap_extractor.fetch import (
    parse_arxiv_feed,
    parse_semantic_scholar_response,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_arxiv_feed_returns_expected_papers():
    xml_text = (FIXTURES / "arxiv_response.xml").read_text()
    papers = parse_arxiv_feed(xml_text)

    assert len(papers) == 2

    first = papers[0]
    assert first.title == "A Study of Low-Resource Neural Machine Translation"
    assert first.source == "arxiv"
    assert first.year == 2021
    assert first.authors == ["Jane Doe", "John Smith"]
    assert "subword tokenization" in first.abstract
    assert first.paper_id == "2101.00001v1"

    second = papers[1]
    assert second.title.startswith("Mutation Testing for Cyber-Physical Systems")
    assert second.authors == ["Alex Lee"]


def test_parse_arxiv_feed_empty():
    empty_feed = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom" '
        'xmlns:arxiv="http://arxiv.org/schemas/atom"></feed>'
    )
    assert parse_arxiv_feed(empty_feed) == []


def test_parse_semantic_scholar_response():
    payload = {
        "data": [
            {
                "title": "Example Paper",
                "abstract": "An example abstract.",
                "authors": [{"name": "A. Researcher"}],
                "year": 2022,
                "url": "https://example.com/paper",
                "paperId": "abc123",
                "venue": "ExampleConf",
                "citationCount": 10,
            }
        ]
    }
    papers = parse_semantic_scholar_response(payload)
    assert len(papers) == 1
    p = papers[0]
    assert p.title == "Example Paper"
    assert p.source == "semantic_scholar"
    assert p.citation_count == 10
    assert p.venue == "ExampleConf"


def test_parse_semantic_scholar_response_handles_missing_abstract():
    payload = {"data": [{"title": "No Abstract Paper", "authors": []}]}
    papers = parse_semantic_scholar_response(payload)
    assert papers[0].abstract == ""
