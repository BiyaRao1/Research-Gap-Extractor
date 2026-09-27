"""Render fetched papers (and optional extracted insights) as JSON or Markdown."""

from __future__ import annotations

import json
from typing import Optional

from .models import ExtractedInsight, Paper


def to_json(papers: list[Paper], insights: Optional[list[ExtractedInsight]] = None) -> str:
    rows = []
    insight_by_title = {i.paper_title: i for i in insights} if insights else {}
    for p in papers:
        row = p.to_dict()
        insight = insight_by_title.get(p.title)
        row["insight"] = insight.to_dict() if insight else None
        rows.append(row)
    return json.dumps(rows, indent=2, ensure_ascii=False)


def to_markdown(papers: list[Paper], insights: Optional[list[ExtractedInsight]] = None) -> str:
    insight_by_title = {i.paper_title: i for i in insights} if insights else {}
    lines: list[str] = []
    for p in papers:
        lines.append(f"## {p.title}")
        meta = f"*{', '.join(p.authors) or 'Unknown authors'}"
        if p.year:
            meta += f" — {p.year}"
        meta += "*"
        lines.append(meta)
        if p.url:
            lines.append(f"[{p.url}]({p.url})")
        lines.append("")
        lines.append(p.abstract or "_No abstract available._")
        lines.append("")

        insight = insight_by_title.get(p.title)
        if insight:
            if insight.one_line_summary:
                lines.append(f"**Summary:** {insight.one_line_summary}")
            if insight.key_methods:
                lines.append("**Key methods:** " + "; ".join(insight.key_methods))
            if insight.stated_limitations:
                lines.append("**Stated limitations:** " + "; ".join(insight.stated_limitations))
            if insight.possible_extensions:
                lines.append("**Possible extensions:**")
                for ext in insight.possible_extensions:
                    lines.append(f"- {ext}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)
