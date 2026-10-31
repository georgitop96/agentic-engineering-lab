# Agentic Engineering Lab

A portfolio of complete, reproducible AI engineering applications.

The first application is the **Financial Research Copilot**, a local-first
tool for asking evidence-backed questions about public financial reports.
It is intentionally being built as a real application: the repository will
document its architecture, tests, limitations, and operational tradeoffs.

## Projects

### Financial Research Copilot

Location: [`projects/financial-research-copilot/`](projects/financial-research-copilot/)

Current status: local PDF extraction, sentence-aware chunking, lexical search,
optional local semantic search, and page-level retrieval evaluation are
implemented. The semantic benchmark remains unmeasured. Answer generation,
answer citations, UI, deployment, and MCP integration remain planned work.
See [project status](docs/PROJECT_STATUS.md) for verification and limitations.

The initial scope is deliberately small:

- ingest a local public or synthetic PDF;
- retrieve relevant passages with page metadata;
- answer one question from retrieved evidence;
- show document and page citations;
- run a deterministic, offline demonstration.

## Repository map

- `projects/` contains maintained, user-facing applications.
- `docs/` contains cross-project architecture and decision records.
- `.github/workflows/` contains automated checks.

## Development baseline

- Python 3.12
- `uv` for environments and dependency locking
- tests that run without credentials or paid API calls

See the project README for setup instructions and the current implementation
status. Planned features are marked explicitly so the portfolio does not imply
capabilities that are not yet available.

## Safety and scope

This portfolio is for software engineering and research assistance. It is not
investment advice and does not place trades, modify accounts, or handle
confidential bank data. External services and paid model calls must be opt-in
and clearly documented.
