"""Fetch paper metadata from arXiv and Semantic Scholar.

Both functions return a list[Paper]. Network calls are isolated here so the
rest of the package (extraction, formatting) can be tested without hitting
the network.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Optional

import requests

from .models import Paper

ARXIV_API = "http://export.arxiv.org/api/query"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"

_ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def parse_arxiv_feed(xml_text: str) -> list[Paper]:
    """Parse an arXiv Atom feed (as returned by the arXiv API) into Papers.

    Kept separate from the HTTP call so it can be unit-tested with a fixture
    string instead of a live request.
    """
    root = ET.fromstring(xml_text)
    papers: list[Paper] = []

    for entry in root.findall("atom:entry", _ARXIV_NS):
        title_el = entry.find("atom:title", _ARXIV_NS)
        summary_el = entry.find("atom:summary", _ARXIV_NS)
        id_el = entry.find("atom:id", _ARXIV_NS)
        published_el = entry.find("atom:published", _ARXIV_NS)

        title = (title_el.text or "").strip().replace("\n", " ")
        abstract = (summary_el.text or "").strip().replace("\n", " ")
        url = (id_el.text or "").strip() if id_el is not None else None
        paper_id = url.rsplit("/", 1)[-1] if url else None

        year: Optional[int] = None
        if published_el is not None and published_el.text:
            year = int(published_el.text[:4])

        authors = [
            (a.find("atom:name", _ARXIV_NS).text or "").strip()
            for a in entry.findall("atom:author", _ARXIV_NS)
            if a.find("atom:name", _ARXIV_NS) is not None
        ]

        papers.append(
            Paper(
                title=title,
                abstract=abstract,
                authors=authors,
                year=year,
                url=url,
                source="arxiv",
                paper_id=paper_id,
            )
        )

    return papers


def search_arxiv(query: str, max_results: int = 10, timeout: int = 15) -> list[Paper]:
    """Search arXiv for `query` and return up to `max_results` papers."""
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    resp = requests.get(ARXIV_API, params=params, timeout=timeout)
    resp.raise_for_status()
    return parse_arxiv_feed(resp.text)


def parse_semantic_scholar_response(payload: dict) -> list[Paper]:
    """Parse a Semantic Scholar `/paper/search` JSON payload into Papers."""
    papers: list[Paper] = []
    for item in payload.get("data", []):
        authors = [a.get("name", "") for a in item.get("authors", []) if a.get("name")]
        papers.append(
            Paper(
                title=item.get("title", "").strip(),
                abstract=(item.get("abstract") or "").strip(),
                authors=authors,
                year=item.get("year"),
                url=item.get("url"),
                source="semantic_scholar",
                paper_id=item.get("paperId"),
                venue=item.get("venue") or None,
                citation_count=item.get("citationCount"),
            )
        )
    return papers


def search_semantic_scholar(
    query: str, max_results: int = 10, timeout: int = 15, api_key: Optional[str] = None
) -> list[Paper]:
    """Search Semantic Scholar for `query` and return up to `max_results` papers."""
    params = {
        "query": query,
        "limit": max_results,
        "fields": "title,abstract,authors,year,url,venue,citationCount",
    }
    headers = {"x-api-key": api_key} if api_key else {}
    resp = requests.get(SEMANTIC_SCHOLAR_API, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return parse_semantic_scholar_response(resp.json())
