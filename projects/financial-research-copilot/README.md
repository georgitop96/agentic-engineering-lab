# Financial Research Copilot

Local-first research assistance for public financial reports.

## Status

This project currently supports local PDF ingestion with page-aware text
extraction. The following remain planned and are not implemented yet:

- evidence-backed answer generation;
- document/page citations;
- multi-document retrieval and evaluation;
- a web UI, deployment, and MCP integrations.

The current v0.1 slice accepts one local PDF, extracts page-aware text, splits
it into deterministic word chunks, and performs local lexical passage search.
It does not make model or network calls.

## Development

From this project directory:

```bash
uv sync
uv run python -m unittest discover -s tests -v
```

Extract the included two-page synthetic fixture:

```bash
uv run frc ingest tests/fixtures/synthetic_report.pdf
```

Example output:

```text
Document: synthetic_report.pdf
Pages: 2

--- Page 1 ---
Revenue increased in 2025.

--- Page 2 ---
Supplier concentration is a risk.
```

To ingest another local PDF, pass its path to the same command:

```bash
uv run frc ingest /path/to/annual-report.pdf
```

Search the included fixture:

```bash
uv run frc search tests/fixtures/synthetic_report.pdf "supplier risk"
```

Example output:

```text
Result 1:
Document: synthetic_report.pdf
Page: 2
Score: 1.00
Passage: Supplier concentration is a risk.
```

Search splits each page into deterministic, non-overlapping chunks of up to 80
words. Each chunk stores its document name, one-based page number, one-based
chunk index, and passage text. Search lowercases word-like terms, scores each
chunk by the fraction of unique query terms it contains, and breaks ties by
document name, page number, and chunk index.

No matches print `No matches found.` and return status 0. Empty queries and
invalid PDF paths print an error and return status 2.

Missing, non-file, invalid, and unreadable PDF paths return a concise error and
exit with status 2.

## Design goals

- reproducible local execution;
- deterministic retrieval where practical;
- citations tied to source document and page metadata;
- explicit insufficient-evidence behavior;
- optional model providers behind a small interface;
- no trading, account, payment, or investment-advice actions.

## Current limitations

- Extraction is text-only; scanned PDFs that contain images without a text
  layer are not OCR'd.
- Text layout, tables, charts, and reading order depend on the PDF's text
  structure and `pypdf` extraction behavior.
- Evidence-backed answer generation and citations beyond page metadata are not
  implemented yet.
