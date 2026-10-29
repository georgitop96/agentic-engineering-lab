# Financial Research Copilot

Local-first research assistance for public financial reports.

## Status

This project currently supports local PDF ingestion with page-aware text
extraction. The following remain planned and are not implemented yet:

- passage retrieval;
- evidence-backed answer generation;
- document/page citations;
- multi-document retrieval and evaluation;
- a web UI, deployment, and MCP integrations.

The current v0.1 slice accepts one local PDF and prints extracted text for each
page with the source filename and one-based page number. It does not make model
or network calls.

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
- Retrieval, citations beyond page metadata, and answer generation are not
  implemented yet.
