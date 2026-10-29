# Portfolio architecture

## Repository boundaries

Each maintained application lives under `projects/` and owns its source,
tests, examples, dependencies, and user-facing documentation. Root `docs/`
contains decisions and principles that apply across projects.

## Financial Research Copilot (planned v0.1)

The first application will use this narrow flow:

```text
local PDF
  -> page-aware extraction
  -> deterministic chunks with document/page metadata
  -> local lexical retrieval
  -> evidence-constrained answerer
  -> validated citations
```

The first implementation should work offline with synthetic or public reports.
An optional model adapter may improve synthesis, but it must not be required
for tests or the reproducible demo.

### Boundaries

- Extraction knows about PDF files, not model providers.
- Retrieval returns evidence records, not prose answers.
- Answering receives only the question and selected evidence.
- Citation formatting is deterministic and independently testable.
- Provider adapters are optional and have explicit timeout, cost, and privacy
  behavior.

### Future layers

Multi-document indexes, hybrid retrieval, evaluation, a UI, deployment, and
MCP integrations are roadmap items. They should be added only after the
single-document path has useful tests and a clear failure mode.
