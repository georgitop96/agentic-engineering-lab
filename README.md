# AI Engineering Lab

A portfolio of practical AI applications built to be installed, inspected, and
evaluated by another engineer.

Each project develops a concrete user workflow with explicit architecture,
reproducible examples, deterministic tests, and documented limitations. The
first project is **Financial Research Copilot**, a local tool for finding
evidence in financial reports.

## First project: Financial Research Copilot

Financial reports spread facts across pages and sections. The Copilot helps a
researcher find relevant passages in one local PDF and inspect their source
pages. Its current release is a retrieval CLI: it returns extracted passages
and page metadata.

| Available now | Planned |
| --- | --- |
| PDF text extraction and sentence-aware chunks | Evidence-backed answer generation and validated answer citations |
| Lexical search and an optional local semantic adapter | Multi-document retrieval and persistent indexes |
| Page retrieval evaluation on a labeled synthetic report | UI, deployment, and MCP integrations |

The current 12-question fixture measures Hit@1 **0.917**, Recall@2
**0.958**, and MRR **0.958**. These are development-fixture results, not
real-world accuracy claims. Lexical and the existing semantic baseline tie on
these aggregate metrics but make different errors; see the
[per-question comparison](docs/PROJECT_STATUS.md#semantic-benchmark).

[Project guide and CLI example](projects/financial-research-copilot/README.md)
· [Verified project status](docs/PROJECT_STATUS.md)
· [Roadmap](docs/roadmap.md)

## Try it locally

Requirements: Python 3.12 and `uv`. From the repository root:

```bash
cd projects/financial-research-copilot
uv sync --locked
uv run --offline --no-sync frc search tests/fixtures/synthetic_financial_report.pdf "ceramic housings"
```

Setup installs the locked project dependencies and may need network access.
After setup, this lexical example runs locally without model weights,
credentials, or paid services. The project guide includes the actual output,
evaluation commands, and tests.

## What this portfolio emphasizes

- Small, explicit interfaces between extraction, retrieval, evaluation, and
  optional model adapters.
- Measurements that can be reproduced, with failure cases and limits stated.
- Offline tests using fixtures and fakes rather than live model APIs.
- Incremental milestones: implemented behavior and future plans are separated.

## Repository guide

| Location | Purpose |
| --- | --- |
| [projects/financial-research-copilot](projects/financial-research-copilot/) | First application: source, tests, fixtures, and locked dependencies |
| [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md) | Verified capabilities, measurements, limitations, and pending work |
| [docs/architecture.md](docs/architecture.md) | Current component boundaries and planned extensions |
| [docs/roadmap.md](docs/roadmap.md) | Completed and upcoming milestones |
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | Test workflow configuration; no remote CI outcome is claimed here |

## Scope and data

Use public or synthetic reports for reproducible examples. PDF text remains
local in the documented retrieval workflow; optional semantic setup may
download model files. This software does not provide investment advice or
perform trades, account changes, payments, or other financial actions.
