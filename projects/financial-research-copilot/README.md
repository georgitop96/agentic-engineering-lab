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
it into deterministic word chunks, and supports local lexical search. Optional
semantic search uses a downloaded local embedding model; the default tests and
lexical workflow do not download model weights or make model API calls.

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

Search splits each page into deterministic sentence-aware chunks with a default
maximum of 80 words. It keeps complete sentences together where practical and
balances sentence groups to avoid tiny trailing fragments. Each chunk stores
its document name, one-based page number, one-based chunk index, and passage
text. Search lowercases word-like terms, scores each chunk by the fraction of
unique query terms it contains, and breaks ties by document name, page number,
and chunk index.

No matches print `No matches found.` and return status 0. Empty queries and
invalid PDF paths print an error and return status 2.

## Optional semantic search

The optional semantic extra uses Qdrant's `fastembed` CPU/ONNX runtime with
`BAAI/bge-small-en-v1.5`. It produces 384-dimensional English vectors; the
optimized ONNX model is approximately 67 MB. Loading it generally needs the
model weights plus several hundred MB of Python/ONNX runtime memory. It is a
practical CPU-local baseline without a GPU/PyTorch requirement, but it is
slower and less transparent than lexical matching and is not finance-specific.

Install the optional dependency when semantic search is explicitly needed:

```bash
uv sync --extra semantic
```

The first semantic search downloads the model into the local model cache. This
is the only model download in the documented workflow; the offline test suite
uses fake vectors and never constructs the model adapter.

Run semantic search with:

```bash
uv run frc search tests/fixtures/synthetic_financial_report.pdf \
  "Can the company cover its near-term obligations?" --method semantic
```

Semantic results display `Cosine similarity`. This is the geometric alignment
between the query and chunk vectors, normally in the range -1 to 1. It is a
ranking signal, not a calibrated probability or confidence score, and should
not be interpreted as the probability that a passage answers a question.
Lexical search remains the default:

```bash
uv run frc search tests/fixtures/synthetic_financial_report.pdf "supplier risk"
```

The semantic interface is separate from lexical retrieval: the CLI reuses
`extract_pdf_pages()` and `chunk_pages()`, then passes the same chunk texts and
query to `FastEmbedder`. `semantic_search()` computes document and query
embeddings through that interface and ranks with cosine similarity. The BGE
adapter adds its documented short-query retrieval instruction to the query only;
passage text is embedded without that prefix.

To explicitly run the model integration smoke test and compare three
paraphrased questions, use:

```bash
uv run python scripts/semantic_smoke.py
```

This command requires the optional dependency and a first-run model download;
it is not part of unit-test discovery or CI.

Inspect chunks from the larger fictional financial report:

```bash
uv run frc chunks tests/fixtures/synthetic_financial_report.pdf --chunk-size 80
```

Each diagnostic result displays the document name, page, chunk index, word
count, and chunk text. The `--chunk-size` option is for inspection; search
continues to use the existing 80-word default unless its code calls the
chunking function with another value. Diagnostic inspection can optionally
repeat complete sentences at chunk boundaries:

```bash
uv run frc chunks tests/fixtures/synthetic_financial_report.pdf \
  --chunk-size 80 --sentence-overlap 1
```

Overlap defaults to zero. It is intentionally not enabled for normal search
until measurements show that the extra duplicate text improves retrieval.

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
- Default chunks are non-overlapping and do not preserve paragraph
  boundaries, character offsets, table structure, or all surrounding context
  at chunk edges. Sentence-aware grouping reduces sentence splits but cannot
  preserve a sentence longer than the configured limit; such a sentence is
  deterministically split into word windows. Optional overlap duplicates
  complete sentences and can increase corpus size, so it is disabled by
  default.
- Semantic similarity can miss exact financial terminology, reflects the
  general model's training distribution, and has no calibrated confidence
  meaning. Model downloads, CPU latency, and local memory use are additional
  operational costs.
- Evidence-backed answer generation and citations beyond page metadata are not
  implemented yet.
