# Financial Research Copilot status

Verified 2026-10-31. Source: [project](../projects/financial-research-copilot/).
This document records the local retrieval evaluation milestone; planned work
below is not implemented functionality.

[Project guide and architecture diagram](../projects/financial-research-copilot/README.md)
· [Portfolio overview](../README.md)
· [Repository roadmap](roadmap.md)

## Current architecture

Python 3.12 with `uv`; `pypdf` is the only required runtime dependency.
`cli.py` coordinates local PDF extraction in `ingestion.py`, deterministic
sentence-aware word chunks in `retrieval.py`, and lexical or optional semantic
ranking. Chunks retain document name, one-based PDF viewer page number, and
chunk index. Printed report page labels are not parsed.

`semantic.py` provides the small `Embedder` interface and optional FastEmbed
adapter for `BAAI/bge-small-en-v1.5`, with cosine ranking. `evaluation.py` loads
JSON labels, validates their page membership, deduplicates ranked chunks into
pages in first-seen order, and calculates per-question metrics and macro means.
The CLI checks the complete dataset and rejects an empty corpus before loading
the optional model. No vector database, LLM answer generation, or persistence
layer is present.

## Verified implemented capabilities

- `frc ingest`: local text-layer PDF extraction with page metadata and errors.
- `frc chunks`: deterministic sentence-aware inspection, size limits, and
  optional complete-sentence overlap (off by default for search).
- `frc search`: lexical term-coverage retrieval; semantic ranking is tested with
  fake vectors. The real FastEmbed adapter is implemented but not benchmarked
  in this milestone.
- `frc eval`: labeled single-PDF page rankings, Hit@1, Recall@2, and MRR,
  per-question and aggregate terminal output, validation against actual page
  numbers, and explicit setup failure when no chunks are extractable.
- Twelve verified questions over the four-page fictional Asteron Ledger
  report: revenue (1), liquidity (2), debt (3), supplier risk (4). Three questions
  require multiple pages, including two with gold pages `[2, 3]` and one `[1, 4]`.

## Evaluation fixture revisions

Question numbers refer to list order in
[financial_report_eval.json](../projects/financial-research-copilot/tests/fixtures/financial_report_eval.json).
All four replacements were chosen before running the revised benchmark.
Gold labels and retrieval algorithms were unchanged.

| Question | Previous wording | Revised wording | Gold and evidence rationale |
| --- | --- | --- | --- |
| 4 | How much cash and equivalents did the company have at year end? | How large was the readily available money balance when the accounting period closed? | Page 2: 74 million cash and equivalents. Removes cash/equivalents/year-end wording while retaining the balance concept. |
| 5 | Can the company draw on an unused revolving credit line? | What borrowing capacity remains untouched at the bank? | Page 2: undrawn 90-million facility. Removes revolving/credit-line wording and asks about the disclosed unused capacity. |
| 7 | What is the reported coverage of interest costs? | By what multiple can earnings meet lenders' financing charges? | Page 3: interest coverage of 6.1 times under the internal calculation. Rephrases the ratio without interest/coverage; it does not request a new ratio calculation. |
| 9 | What sourcing response is planned for ceramic housings? | How is management reducing dependence on a single maker of protective enclosures? | Page 4: qualifying a second source for ceramic housings. Uses enclosures as a paraphrase of housings and removes ceramic/sourcing anchors. |

These are manual relevance judgments, not independently adjudicated labels.
Generic keyword overlap remains possible; paraphrase success alone does not
establish semantic reasoning.

## Test and evaluation results

All **41 tests passed**, preserving the previous 33 tests. Added coverage
includes heterogeneous macro averages, a zero-result question in the mean,
invalid label types and values, nonexistent pages, nonconsecutive actual page
numbers, empty extracted text, and semantic CLI wiring with fake vectors.
`git diff --check` passed. No formatter or type checker is configured.

Real lexical runs before and after the four question revisions:

| Fixture version | Questions | Hit@1 | Recall@2 | MRR |
| --- | ---: | ---: | ---: | ---: |
| Before revisions | 12 | 1.000 | 0.958 | 1.000 |
| Current fixture | 12 | 0.917 | 0.958 | 0.958 |

The current command reproduces the second row. The first row is the recorded
pre-edit measurement. Question 9 now ranks gold page 4 second, reducing Hit@1
and MRR. Question 12 still retrieves `4,3,1,2` against gold `[1,4]`, producing
Recall@2 of 0.5. The other 11 questions have Recall@2 of 1. No retrieval or
chunking algorithm was adjusted to optimize these numbers.

Commands executed from `projects/financial-research-copilot`, using the
existing project environment without syncing or installing dependencies:

```bash
UV_CACHE_DIR=/tmp/frc-uv-cache UV_PYTHON_DOWNLOADS=never PYTHONDONTWRITEBYTECODE=1 uv run --offline --no-sync python -m unittest discover -s tests -v
UV_CACHE_DIR=/tmp/frc-uv-cache UV_PYTHON_DOWNLOADS=never PYTHONDONTWRITEBYTECODE=1 uv run --offline --no-sync frc eval tests/fixtures/synthetic_financial_report.pdf --method lexical --dataset tests/fixtures/financial_report_eval.json
git diff --check
```

Metric formulas and zero-result behavior are defined in the
[project README](../projects/financial-research-copilot/README.md#reproducible-page-level-evaluation).

## Known limitations

- This is a four-page synthetic development fixture, not a real-world accuracy
  benchmark. Twelve manually chosen questions and one topic per page limit
  discrimination; there is no held-out test set or unanswerable-question label.
- Evaluation measures page retrieval, not passage sufficiency or answer
  correctness. Hit@1 and MRR need only one gold page, so they do not measure
  complete multi-page evidence. Evaluation ranks all chunks; normal search
  defaults to five results.
- No OCR, reliable table/footnote reconstruction, multi-document retrieval,
  numerical answer validation, or evidence-backed answer generation exists.
- Labels are checked against extracted page metadata, not a document hash;
  using another PDF with the same page numbers can still give meaningless
  results. The fixture assumes this exact synthetic report.
- Lexical matching includes common words and tie-breaks by source metadata;
  results are deterministic but can favor incidental word overlap.
- Semantic similarity is not calibrated confidence. The current evaluation
  re-embeds the corpus for every question; production latency is not measured.
- Lexical evaluation needs no model API, secret, or paid service and keeps PDF
  text local. Semantic inference is local, but model setup may require a
  separate download, CPU time, memory, and disk space. No download or paid call
  was made for this milestone.

## Pending semantic benchmark

**Not yet measured.** At review FastEmbed was installed, but its default
`/tmp/fastembed_cache` was absent, no cache override was configured, and the
inspected Hugging Face cache contained no ONNX weights. Mocked tests establish
wiring, not real-model quality or performance. No semantic scores are claimed.

With the existing dependency and configured weights already cached, run from
the project directory:

```bash
HF_HUB_OFFLINE=1 uv run --offline --no-sync frc eval tests/fixtures/synthetic_financial_report.pdf --method semantic --dataset tests/fixtures/financial_report_eval.json
```

This command requires no dependency installation and forbids model downloads.
Record the exact environment and per-question results when that prerequisite
is met; compare methods on the same current dataset.

## Next planned milestones

1. Measure the existing semantic baseline on the current labeled dataset when
   local weights are available.
2. Broaden independently labeled evaluation with harder financial evidence,
   ratios, and insufficient-evidence cases before selecting retrieval changes.
3. Plan evidence-constrained answers with validated page citations and an
   insufficient-evidence response path, tested with deterministic fakes.

These milestones remain planned; this evaluation change implements none of
them. No commit, push, deployment, or external financial action was performed.
