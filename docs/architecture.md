# Portfolio architecture

## Repository boundaries

Each maintained application lives under `projects/` and owns its source,
tests, examples, dependencies, and user-facing documentation. Root `docs/`
contains decisions and principles that apply across projects.

## Financial Research Copilot: implemented retrieval path

The current CLI coordinates these local components:

```text
local PDF
  -> ingestion.py: page-aware pypdf extraction
  -> retrieval.py: deterministic sentence-aware chunks
  -> lexical ranking OR semantic.py: optional FastEmbed/cosine ranking
  -> CLI passages with document/page metadata

JSON questions and gold pages + actual extracted page numbers
  -> evaluation.py: gold-page validation
  -> per-question retrieval using all ranked chunks
  -> unique page ranks in first-seen order
  -> Hit@1, Recall@2, MRR and terminal table
```

Lexical retrieval and tests run offline after dependency setup. Semantic
inference uses the optional local model; cached weights are required for an
offline semantic run. There is no vector database or persistent index.
See the [project guide](../projects/financial-research-copilot/README.md#current-architecture)
for the Mermaid diagram and [verified status](PROJECT_STATUS.md) for measured
capabilities and limitations.

### Boundaries

- Extraction knows about PDF files, not model providers.
- Retrieval returns evidence records, not prose answers.
- Evaluation compares page rankings with manual labels; it does not evaluate
  generated answers or validate the sufficiency of a retrieved passage.
- The optional embedding adapter implements a small interface and keeps model
  inference separate from lexical retrieval.

### Planned extensions (not implemented)

Evidence-constrained answering and validated answer citations are future
layers. The intended boundary is to pass only the question and selected
evidence to an answerer, then validate its output and citations independently.
An insufficient-evidence answer path must accompany that feature.

Broader evaluation, multi-document indexes, hybrid retrieval, a UI, deployment,
and MCP integrations remain roadmap work. These do not appear in the current
retrieval execution path.
