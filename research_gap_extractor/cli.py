"""Command-line interface.

Examples
--------
Search arXiv only, no LLM extraction, print Markdown:

    python -m research_gap_extractor search "low-resource neural machine translation" \\
        --source arxiv --limit 5 --format markdown

Search both sources, extract research gaps with Claude, save JSON:

    export ANTHROPIC_API_KEY=sk-...
    python -m research_gap_extractor search "mutation testing cyber-physical systems" \\
        --source both --limit 5 --extract --format json --out results.json
"""

from __future__ import annotations

import argparse
import sys

from .extract import AnthropicClient, extract_insights
from .fetch import search_arxiv, search_semantic_scholar
from .models import Paper
from .report import to_json, to_markdown


def _dedupe(papers: list[Paper]) -> list[Paper]:
    seen: set[str] = set()
    unique: list[Paper] = []
    for p in papers:
        key = p.title.strip().lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="research_gap_extractor",
        description="Search arXiv / Semantic Scholar and (optionally) extract "
        "research gaps with an LLM.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search", help="Search for papers on a topic")
    search.add_argument("query", help="Search query, e.g. 'mutation testing'")
    search.add_argument(
        "--source", choices=["arxiv", "semantic_scholar", "both"], default="both"
    )
    search.add_argument("--limit", type=int, default=5, help="Max results per source")
    search.add_argument(
        "--extract", action="store_true", help="Run LLM extraction on each result"
    )
    search.add_argument(
        "--model", default="claude-sonnet-4-5", help="Model name for --extract"
    )
    search.add_argument("--format", choices=["json", "markdown"], default="markdown")
    search.add_argument("--out", help="Write output to this file instead of stdout")

    return parser


def run_search(args: argparse.Namespace) -> int:
    papers: list[Paper] = []
    if args.source in ("arxiv", "both"):
        try:
            papers.extend(search_arxiv(args.query, max_results=args.limit))
        except Exception as exc:  # noqa: BLE001 - surface network errors plainly
            print(f"[warn] arXiv search failed: {exc}", file=sys.stderr)
    if args.source in ("semantic_scholar", "both"):
        try:
            papers.extend(search_semantic_scholar(args.query, max_results=args.limit))
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] Semantic Scholar search failed: {exc}", file=sys.stderr)

    papers = _dedupe(papers)

    if not papers:
        print("No papers found.", file=sys.stderr)
        return 1

    insights = None
    if args.extract:
        client = AnthropicClient(model=args.model)
        insights = extract_insights(papers, client)

    output = to_json(papers, insights) if args.format == "json" else to_markdown(papers, insights)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Wrote {len(papers)} paper(s) to {args.out}")
    else:
        print(output)

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "search":
        return run_search(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
