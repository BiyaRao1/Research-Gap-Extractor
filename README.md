# research-gap-extractor

Search [arXiv](https://arxiv.org) and [Semantic Scholar](https://www.semanticscholar.org)
for papers on a topic, then use an LLM to pull out **structured research
gaps, stated limitations, and possible extensions** from each abstract —
grounded only in what the abstract actually says.

Built while scoping PhD research directions across software testing, NLP and
applied ML: instead of reading through dozens of abstracts by hand to find a
concrete angle for a research proposal, this tool turns a topic query into a
short, structured list of "what's missing" and "what could be tried next."

## Why

Reading abstracts to find open problems is repetitive and easy to do
inconsistently. This tool standardizes the process:

1. Pull recent, relevant papers for a topic from two sources.
2. For each one, ask an LLM to extract (not invent) the methods used, the
   limitations the authors themselves stated, and concrete follow-up
   directions consistent with the abstract.
3. Get the result as Markdown (for reading) or JSON (for further processing).

## Install

```bash
git clone https://github.com/<your-username>/research-gap-extractor.git
cd research-gap-extractor
pip install -r requirements.txt        # core (search only)
pip install -r requirements-dev.txt    # + pytest, + anthropic (for --extract)
```

## Usage

Search only, no LLM call, Markdown to stdout:

```bash
python -m research_gap_extractor search "low-resource neural machine translation" \
    --source arxiv --limit 5 --format markdown
```

Search both sources and extract structured gaps with Claude, save to a file:

```bash
export ANTHROPIC_API_KEY=sk-...
python -m research_gap_extractor search "mutation testing cyber-physical systems" \
    --source both --limit 5 --extract --format json --out results.json
```

See [`examples/sample_output.md`](examples/sample_output.md) for the shape
of `--extract` output.

### CLI options

| Flag | Description |
|---|---|
| `query` | Search query (required, positional) |
| `--source` | `arxiv`, `semantic_scholar`, or `both` (default: `both`) |
| `--limit` | Max results per source (default: `5`) |
| `--extract` | Run LLM extraction on each result (requires `ANTHROPIC_API_KEY`) |
| `--model` | Model name for `--extract` (default: `claude-sonnet-4-5`) |
| `--format` | `markdown` or `json` (default: `markdown`) |
| `--out` | Write to a file instead of stdout |

## Design

- `fetch.py` — HTTP calls to arXiv/Semantic Scholar, isolated from parsing
  so the parsers are testable without the network.
- `extract.py` — provider-agnostic `LLMClient` protocol plus a working
  `AnthropicClient`; prompt-building and response-parsing are pure functions,
  independent of any live API call.
- `report.py` — renders `Paper` + `ExtractedInsight` objects to Markdown or
  JSON.
- `cli.py` — thin argument-parsing layer over the above.

This split means the whole pipeline except the actual network/LLM calls is
covered by fast, offline unit tests (see `tests/`, run with `pytest`).

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

14 tests, all offline (fixture-based arXiv XML, a fake LLM client) — no API
key or network access required to run the suite.

## Possible extensions

- Cache fetched papers locally to avoid re-querying on repeated searches.
- Add a `--dedupe-by-doi` mode for more reliable cross-source deduplication.
- Support Google Scholar via `scholarly` as a third source.
- Rank extracted "possible extensions" by novelty against a personal
  bibliography.

## License

MIT — see [LICENSE](LICENSE).
