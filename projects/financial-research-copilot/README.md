# Financial Research Copilot

Local-first research assistance for public financial reports.

## Status

This project is currently a tested Python package scaffold. The following are
planned and not implemented yet:

- PDF ingestion and page-aware extraction;
- passage retrieval;
- evidence-backed answer generation;
- document/page citations;
- multi-document retrieval and evaluation;
- a web UI, deployment, and MCP integrations.

The target v0.1 is one local PDF, one question, retrieved evidence, and a
cited answer. The demo will use synthetic or public data and will not require
confidential bank data, credentials, or paid API calls.

## Development

From this project directory:

```bash
uv sync
PYTHONPATH=src uv run --no-project python -m unittest discover -s tests -v
```

The current baseline test verifies that the package can be imported. It does
not imply that the copilot features are available yet.

## Design goals

- reproducible local execution;
- deterministic retrieval where practical;
- citations tied to source document and page metadata;
- explicit insufficient-evidence behavior;
- optional model providers behind a small interface;
- no trading, account, payment, or investment-advice actions.
