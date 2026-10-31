# Roadmap

The roadmap is intentionally incremental. An item is not presented as a
capability until it has implementation, tests, and documentation.

## Financial Research Copilot

- [x] v0.1: extract text from one local PDF with page metadata.
- [x] v0.1: retrieve relevant passages locally with lexical search.
- [x] Optional local semantic adapter with deterministic fake-vector tests.
- [x] Page retrieval evaluation with validated labels and offline lexical results.
- [x] Reproducible synthetic-report CLI search and evaluation examples.
- [x] Measure the existing semantic adapter on the same evaluation fixture.
- [ ] Broaden independently labeled evidence and insufficient-evidence cases.
- [ ] Test hybrid retrieval against both baselines on a broader evaluation set.
- [ ] v0.1: return one evidence-backed answer with citations.
- [ ] v0.2: support multiple documents and persistent local indexes.
- [ ] v0.2: broaden retrieval evaluation and add answer evaluation.
- [ ] v0.3: add a small user interface.
- [ ] Later: deployment and MCP integrations with explicit permissions.

Checked items describe implemented functionality; they do not claim a measured
semantic quality advantage. See [project status](PROJECT_STATUS.md) for local
verification and [the project guide](../projects/financial-research-copilot/README.md)
for commands and limitations.
