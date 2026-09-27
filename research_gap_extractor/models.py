"""Data models used across the package."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Paper:
    """A single paper's metadata, normalized across sources."""

    title: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    url: Optional[str] = None
    source: str = "unknown"  # "arxiv" | "semantic_scholar"
    paper_id: Optional[str] = None
    venue: Optional[str] = None
    citation_count: Optional[int] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExtractedInsight:
    """Structured output of the gap-extraction step for one paper."""

    paper_title: str
    key_methods: list[str] = field(default_factory=list)
    stated_limitations: list[str] = field(default_factory=list)
    possible_extensions: list[str] = field(default_factory=list)
    one_line_summary: str = ""
    raw_model_output: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
