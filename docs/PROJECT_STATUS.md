# Financial Research Copilot status

Verified 2026-10-31. Source: [project](../projects/financial-research-copilot/).
This document records the local lexical and semantic evaluation baselines; planned work
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
- `frc search`: lexical term-coverage retrieval and real local FastEmbed
  retrieval, with deterministic fake-vector unit tests and the synthetic
  semantic benchmark recorded below.
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
  separate download, CPU time, memory, and disk space. Only the configured
  public model was downloaded for the semantic benchmark; no paid call was made.

## Semantic benchmark

Measured 2026-10-31 against clean HEAD `5711af4` using the unchanged current
12-question fixture and four-page PDF. All 41 tests passed again; lexical
results reproduced the committed baseline. No dependencies, dataset, retrieval
algorithms, query instruction, or model selection were changed.

### Model and environment

- Python 3.12.16, FastEmbed 0.9.1, ONNX Runtime 1.31.1, pypdf 6.21.4,
  huggingface-hub 1.33.0; existing project `.venv`, CPU inference.
- Application model: `BAAI/bge-small-en-v1.5`. FastEmbed resolves it to
  `Qdrant/bge-small-en-v1.5-onnx-Q`, revision
  `aa8f8b060edb00e03bfdd08813a2949946c8ba55`.
- `model_optimized.onnx`: 66,465,124 bytes; SHA256
  `51f1bd0addd6e859e42c2c8021a5e5461385bb676a649f4b269aa445449f2431`.
  Only this model and four supporting files (`config.json`, `tokenizer.json`,
  `tokenizer_config.json`, `special_tokens_map.json`) were fetched.
- Vectors are 384-dimensional. The cached tokenizer lowercases and uses a
  512-token limit. The installed ONNX adapter takes the first token for
  three-dimensional outputs and normalizes embeddings.
- Query text is prefixed with
  `Represent this sentence for searching relevant passages: `; passages are
  the unchanged chunk texts without a prefix. The app calls `embed()` for both.
- Ranking uses cosine similarity, descending, with document/page/chunk
  tie-breakers. There is no relevance threshold; semantic ranks every chunk,
  while lexical omits chunks with no matching terms. Evaluation requests all
  chunks (seven here), then retains unique pages in first-seen order.

### Persistent cache and exact commands

The configured model was loaded once into
`/home/georg/.cache/financial-research-copilot/fastembed`, outside Git. Existing
code honors `FASTEMBED_CACHE_PATH`; otherwise installed FastEmbed uses
`tempfile.gettempdir()/fastembed_cache` (`/tmp/fastembed_cache` here). The
directory persists, but the environment variable must be set in each new
shell. No startup file or credentials were added. Cache reuse is explicit
below, not dependent on a temporary directory.

From `projects/financial-research-copilot`, these are the executed settings
and commands (the environment assignments are grouped here for readability):

```bash
export UV_CACHE_DIR=/tmp/frc-uv-cache
export UV_PYTHON_DOWNLOADS=never
export PYTHONDONTWRITEBYTECODE=1
uv run --offline --no-sync python -m unittest discover -s tests -v
uv run --offline --no-sync frc eval tests/fixtures/synthetic_financial_report.pdf --method lexical --dataset tests/fixtures/financial_report_eval.json

export FASTEMBED_CACHE_PATH=/home/georg/.cache/financial-research-copilot/fastembed
export HF_HUB_DISABLE_IMPLICIT_TOKEN=1
export HF_HUB_DISABLE_TELEMETRY=1
export HF_HUB_DISABLE_XET=1
# One-time initialization: allows only the model library to fetch its files.
# uv remains offline and --no-sync prevents dependency installation.
uv run --offline --no-sync python -c 'from financial_research_copilot.semantic import FastEmbedder, DEFAULT_MODEL_NAME; model = FastEmbedder(); print("Loaded configured model:", DEFAULT_MODEL_NAME)'

# Subsequent evaluation uses the cached model without network access.
HF_HUB_OFFLINE=1 uv run --offline --no-sync frc eval tests/fixtures/synthetic_financial_report.pdf --method semantic --dataset tests/fixtures/financial_report_eval.json
git diff --check
```

For another WSL user, set the cache to
`"$HOME/.cache/financial-research-copilot/fastembed"` instead. This is a model
cache, not a persisted document index. The application does not pin a model
revision, so a future fresh download should be checked against the identity
above before claiming an identical environment.

### Aggregate and per-question results

| Method | Hit@1 | Recall@2 | MRR |
| --- | ---: | ---: | ---: |
| Lexical | 0.917 | 0.958 | 0.958 |
| Semantic | 0.917 | 0.958 | 0.958 |

Question numbers match the unchanged JSON list. Ranked columns contain all
retrieved unique pages. `H1 L/S` shows first-page success for lexical/semantic
(1 = success, 0 = failure); `R2 L/S` shows the fraction of gold pages found in
the first two unique pages. A fraction below 1 means incomplete evidence.

| Q / topic | Gold | Lexical pages | Semantic pages | H1 L/S | R2 L/S | Semantic effect on metrics |
| --- | --- | --- | --- | --- | --- | --- |
| 1 / 2025 revenue | 1 | 1,2,3 | 1,2,3,4 | 1/1 | 1/1 | Tie |
| 2 / revenue increase | 1 | 1,2,4 | 2,1,3,4 | 1/0 | 1/1 | Hurts: reciprocal rank 1 to 0.5 |
| 3 / 62-million activity | 1 | 1,2,3 | 1,2,3,4 | 1/1 | 1/1 | Tie |
| 4 / available money | 2 | 2,3,1,4 | 2,3,4,1 | 1/1 | 1/1 | Tie |
| 5 / untouched borrowing | 2 | 2,3,4,1 | 2,3,4,1 | 1/1 | 1/1 | Tie |
| 6 / 2026 principal | 3 | 3,1,4,2 | 3,2,1,4 | 1/1 | 1/1 | Tie |
| 7 / financing charges | 3 | 3 | 3,2,1,4 | 1/1 | 1/1 | Tie |
| 8 / biggest supplier share | 4 | 4,1,2,3 | 4,1,3,2 | 1/1 | 1/1 | Tie |
| 9 / protective enclosures | 4 | 1,4,2,3 | 4,2,3,1 | 0/1 | 1/1 | Helps: reciprocal rank 0.5 to 1 |
| 10 / cash versus debt | 2,3 | 3,2,4,1 | 2,3,1,4 | 1/1 | 1/1 | Tie |
| 11 / cash flow versus payments | 2,3 | 2,3,1,4 | 3,2,1,4 | 1/1 | 1/1 | Tie |
| 12 / growth and disruption | 1,4 | 4,3,1,2 | 4,2,3,1 | 1/1 | 0.5/0.5 | Tie on metrics; second gold rank 3 to 4 |

### Interpretation and execution notes

Semantic helps Q9 and hurts Q2; the other ten questions tie on the measured
metrics, including the incomplete multi-page Q12. For Q2, an additional offline
search confirmed that the liquidity/cash-growth passage scores 0.5450 versus
0.5416 for the revenue page. This is a close ranking error, not evidence of a
known causal mechanism. Semantic also ranks every page for Q7 where lexical
returns only page 3; these metrics do not penalize the extra irrelevant tail.

The four-page, one-topic-per-page fixture has high topic separation and few
negatives; multi-page gold sets also make finding any relevant page easier.
Equal averages hide offsetting mistakes. Neither statistical superiority nor
generalizability follows from 12 manual questions. Page hits do not establish
chunk sufficiency, numeric accuracy, or complete multi-page evidence.

Complementary Q2/Q9 errors justify a controlled hybrid experiment after
expanding independently labeled evaluation, not an assumption that combining
rankings will help. A fixed rank-fusion baseline should be compared with both
methods on held-out questions without tuning on this fixture. No hybrid
algorithm was implemented or measured here.

Both CLI evaluations completed successfully. The unauthenticated model fetch
printed a Hugging Face rate-limit advisory, but required no token. ONNX Runtime
printed a warning that its telemetry device ID could not be persisted and it
used an in-memory identifier; inference and evaluation still exited 0. No
runtime fix was needed. Unit tests logged the expected invalid-PDF diagnostics
and passed. Latency and peak memory were not benchmarked.

## Next planned milestones

1. Broaden independently labeled evaluation with harder financial evidence,
   ratios, and insufficient-evidence cases before selecting retrieval changes.
2. Test a simple hybrid rank-fusion baseline against lexical and semantic
   retrieval on the broader set, without optimizing this 12-question fixture.
3. Plan evidence-constrained answers with validated page citations and an
   insufficient-evidence response path, tested with deterministic fakes.

These milestones remain planned; this evaluation change implements none of
them. No commit, push, deployment, or external financial action was performed.
