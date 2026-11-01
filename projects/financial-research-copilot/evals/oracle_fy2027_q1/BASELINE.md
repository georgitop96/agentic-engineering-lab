# Milestone 5B — Oracle development retrieval baseline

Measured 2026-11-01 against repository base `d2aab98`. This is a diagnostic
baseline on the 15 development questions, not an answer-accuracy evaluation or
a holdout comparison. The dataset remains pending human rendered-PDF review
and source provenance approval; this run does not approve or freeze it.

## Scope and compatibility

Git was clean before the run. The local source is
`data/oracle_fy2027_q1_10q.pdf` (50 physical pages), SHA256
`3c9e939c3ac86d28b8047b5308b2fb8dfa6f859ace9ef452f2a2d0f1715474ff`,
matching `annotations.json`. `development.json` loads as 15 unique Q01–Q15
items; their annotation assignments and PDF page labels validate.

The existing CLI is compatible with the Oracle question schema: it reads
`question` and `gold_pages`, ignoring the extra `id`. No application code change
was needed. It does **not** consume reference answers, sufficient-page groups,
or mandatory-evidence annotations. Those are evaluation limitations, not JSON
loading failures. Question IDs below are joined from development metadata.

Only development queries were executed. The full PDF remained the searchable
corpus, including distractor pages. The holdout file was not opened, scored,
tuned against or changed. Gold labels and annotations were not changed.

## Fixed configuration and reproduction

- Existing project `.venv`: Python 3.12.16, pypdf 6.21.4, FastEmbed 0.9.1,
  ONNX Runtime 1.31.1, huggingface-hub 1.33.0. No installation or paid API calls.
- Ordinary PDF text extraction; default sentence-aware chunks, maximum 80
  words, zero overlap: **401 chunks across 50 pages**. Overlong sentences/tables
  fall back to word windows. No table-aware extraction or header propagation.
- Lexical: fraction of unique query terms present, including common words;
  zero-match chunks omitted. Semantic: existing cosine ranking and query-only
  prefix `Represent this sentence for searching relevant passages: `.
- Semantic model: `BAAI/bge-small-en-v1.5`, resolving to cached quantized
  `Qdrant/bge-small-en-v1.5-onnx-Q`, revision
  `aa8f8b060edb00e03bfdd08813a2949946c8ba55`. Verified ONNX file:
  66,465,124 bytes, SHA256
  `51f1bd0addd6e859e42c2c8021a5e5461385bb676a649f4b269aa445449f2431`.
- Both methods request all chunks, then deduplicate pages in first-seen order;
  existing document/page/chunk tie-breakers remain unchanged. Default search's
  five-chunk cutoff is not used for these CLI evaluation scores.
- Offline local CPU inference using the existing persistent cache; no source
  text was sent to a remote service. ONNX Runtime logged a nonfatal inability
  to persist its telemetry device ID; inference continued.

From `projects/financial-research-copilot`:

```bash
.venv/bin/frc eval data/oracle_fy2027_q1_10q.pdf \
  --method lexical --dataset evals/oracle_fy2027_q1/development.json
HF_HUB_OFFLINE=1 \
FASTEMBED_CACHE_PATH=/home/georg/.cache/financial-research-copilot/fastembed \
.venv/bin/frc eval data/oracle_fy2027_q1_10q.pdf \
  --method semantic --dataset evals/oracle_fy2027_q1/development.json
.venv/bin/python -m unittest discover -s tests -v
```

Use an equivalent existing cache path on another machine. Without these exact
local PDF bytes and cached model, the run is not reproducible as recorded.
The measured runs called the existing `cli.main()` through a temporary
instrumentation wrapper that captured returned chunks, timings and scores;
the original retrieval functions executed unchanged on every question. Raw
CLI output and structured diagnostics were written under `/tmp`, outside Git.

## Metric interpretation

Hit@1 tests whether the first unique page is any gold page. Recall@2 divides
gold pages found in the first two unique pages by the flat gold-page count.
MRR uses the first gold page anywhere in the full unique-page ranking. All
three are macro-averaged across 15 questions. None checks arithmetic, table
alignment, citations, answer correctness or completeness of supporting text.

An additional diagnostic counts a question complete at page depth k only if
at least one annotated `minimal_sufficient_page_sets` group is contained in
the first k unique pages. This preserves alternatives (Q06: p18 alone OR
p23+p24) versus conjunctions (Q02: p3+p7+p8 all required). It is a **page-set
coverage proxy**, not passage-level evidence recovery. Q02 cannot complete
at depth two; Q06's flat Recall@2 cannot reach 1 even when p18 suffices.
There are six mandatory multi-page development items: Q02, Q04, Q07, Q09,
Q12 and Q14.

## Results

| Method | Hit@1 | Recall@2 | MRR | Sufficient page set @2 | Sufficient page set @5 | Mandatory sets @2 | Mandatory sets @5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Lexical | 0.600 | 0.511 | 0.712 | 8/15 | 12/15 | 2/6 | 5/6 |
| Semantic | 0.667 | 0.600 | 0.780 | 8/15 | 11/15 | 1/6 | 3/6 |

Semantic gains one first-page hit (Q02); it improves early gold-page ranks for Q01 and Q03, but regresses on Q04 and Q08. All-item page-set coverage at depth two ties at 8/15. Lexical completes more mandatory sets at depth five (5/6 versus 3/6). These are different questions answered by different metrics, so the higher semantic page averages do not establish more complete evidence retrieval.

Observed wall time was 4.22s lexical and 436.97s semantic (approximately 7.3 minutes). Semantic retrieval calls totaled 431.83s, re-embedding the 401 chunks on each of 15 queries. These are single-run observations, including instrumentation; not controlled latency benchmarks. Memory was not profiled.

Development JSON SHA256:
`e5501f504c4be0a1f76dd661149b81ba8fd357bfe677cad3d2def2fd902a9a9a`.
Annotation JSON SHA256:
`545c4de652ce1ca093e19bfe7aec9d4df2ece8f9b1869d01f70eb0a0c1336abc`.

## Per-question rankings and scores

Top five **unique PDF pages**, in order. H/R/M = Hit@1 / Recall@2 / MRR, rounded to three decimals. Complete depth is the first unique-page rank containing any complete annotated sufficient set (lexical / semantic), not the first correct passage. `+` requires both/all pages; `or` denotes alternatives.

| ID | Sufficient pages | Lexical top 5 | Semantic top 5 | Lexical H/R/M | Semantic H/R/M | Complete depth L/S |
| --- | --- | --- | --- | --- | --- | --- |
| Q01 | 3 | 9, 13, 8, 11, 16 | 35, 3, 11, 10, 7 | 0.000 / 0.000 / 0.125 | 0.000 / 1.000 / 0.500 | 8 / 2 |
| Q02 | 3+7+8 | 35, 36, 3, 5, 7 | 8, 7, 35, 3, 2 | 0.000 / 0.000 / 0.333 | 1.000 / 0.667 / 1.000 | 8 / 4 |
| Q03 | 4 or 28 | 29, 7, 36, 8, 33 | 29, 28, 33, 35, 32 | 0.000 / 0.000 / 0.059 | 0.000 / 0.500 / 0.500 | 17 / 2 |
| Q04 | 7+9 | 35, 36, 9, 34, 7 | 36, 35, 34, 15, 37 | 0.000 / 0.000 / 0.333 | 0.000 / 0.000 / 0.143 | 5 / 16 |
| Q05 | 7 or 36 | 36, 2, 5, 7, 14 | 36, 33, 35, 7, 8 | 1.000 / 0.500 / 1.000 | 1.000 / 0.500 / 1.000 | 1 / 1 |
| Q06 | 18 or 23+24 | 18, 24, 23, 9, 13 | 23, 21, 18, 24, 30 | 1.000 / 0.667 / 1.000 | 1.000 / 0.333 / 1.000 | 1 / 3 |
| Q07 | 9+37 | 37, 8, 9, 15, 34 | 9, 7, 4, 12, 8 | 1.000 / 0.500 / 1.000 | 1.000 / 0.500 / 1.000 | 3 / 6 |
| Q08 | 13 | 8, 9, 13, 3, 11 | 9, 3, 4, 10, 7 | 0.000 / 0.000 / 0.333 | 0.000 / 0.000 / 0.062 | 3 / 16 |
| Q09 | 14+15 | 15, 14, 12, 37, 23 | 14, 12, 15, 8, 16 | 1.000 / 1.000 / 1.000 | 1.000 / 0.500 / 1.000 | 2 / 3 |
| Q10 | 15 | 15, 29, 34, 37, 13 | 15, 37, 35, 33, 9 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 1 / 1 |
| Q11 | 15 or 37 | 6, 15, 37, 21, 7 | 6, 37, 15, 21, 3 | 0.000 / 0.500 / 0.500 | 0.000 / 0.500 / 0.500 | 2 / 2 |
| Q12 | 12+13 | 13, 12, 8, 15, 29 | 13, 12, 33, 29, 20 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 2 / 2 |
| Q13 | 17 | 17, 7, 29, 9, 16 | 17, 7, 12, 10, 20 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 1 / 1 |
| Q14 | 19+20 | 20, 27, 7, 19, 29 | 20, 27, 28, 29, 26 | 1.000 / 0.500 / 1.000 | 1.000 / 0.500 / 1.000 | 4 / 6 |
| Q15 | 30 | 30, 33, 32, 28, 31 | 30, 31, 32, 25, 28 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 1 / 1 |

### Specific ranking failures

- **Q01:** lexical first reaches p3 at unique-page rank 8; semantic reaches it at rank 2 after the p35 working-capital summary. Semantic’s first p3 chunk is c2, which still lacks both required totals.
- **Q02:** semantic retrieves restricted cash p8 and cash-flow p7 first, but needs p3 at rank 4 for the reconciliation. Lexical completes the three-page set only at rank 8.
- **Q03:** both first select p29’s GAAP adjustments table. Semantic reaches alternative p28 at rank 2 (lexical first gold rank 17), but its first p28 chunk is c6, a growth narrative without the requested operating-margin inputs.
- **Q04:** liquidity/free-cash-flow discussion dominates. Semantic first reaches any gold page at rank 7 and completes p7+p9 only at rank 16; lexical completes at rank 5.
- **Q06:** both Hit@1 scores are 1, but semantic’s p23 hit alone is an incomplete alternative path; its first complete page set appears at depth 3.
- **Q07:** both Hit@1 scores are 1, retrieving different halves of the answer. Lexical completes p9+p37 at depth 3; semantic needs depth 6.
- **Q08:** lexical reaches p13 at rank 3; semantic first returns RPO on p9 and reaches p13 only at rank 16. Even semantic’s first p13 hit is the unrelated restructuring table c1; the deferred-revenue table is c6.
- **Q09:** lexical completes p15+p14 in two pages; semantic needs three, and its first p15 passage is the recognized lease-maturity table c1 rather than unrecognized commitments c2. Both first select p14 c2 rather than the ROU-additions row c4.
- **Q11:** both favor the stockholders’ equity table p6 before the scoped rounded ATM disclosures. The table’s monetary value must not be mistaken for a share count.
- **Q12:** both achieve perfect flat page metrics, yet the first p13 passage lacks the required total-cost inputs.
- **Q14:** both select p20 first, but its first chunk lacks pretax income; p19 first appears as a footnote chunk, at unique-page rank 4 lexical / 6 semantic.
- **Q15:** both achieve perfect flat metrics via the causal paragraph, which omits the numeric inputs. Q05 and Q10 provide useful counterexamples: both methods return self-contained financial tables first.

## Extraction and retrieved-passage findings

The following observations come from ordinary extracted text, default chunks
and returned passages, not rendered-PDF inspection:

- **Broken row labels and missing context:** p3 c2 ends `Total current`, c3
  begins `assets 55,630 46,567` and ends another `Total current`, and c4 begins
  `liabilities 47,514 41,764`. The two Q01 inputs and their full row labels
  cannot be found in one chunk. Dates and units are in c2, not c3/c4.
- **Headers separated from inputs:** Q04's p7 c2 has the prepayment and
  operating-cash-flow rows, while the period/unit header is c1. Q05's p7
  operating cash flow and capex land in c2 and c3; its alternative p36 c9
  retains a self-contained calculation table. Q09's p14 c4 has ROU additions,
  but its header is in c3. A page hit alone cannot validate units or columns.
- **Restructuring totals separated from headers:** p13 c1 holds headers and
  the start of the table; c2 has the $1,971m/$2,103m totals needed by Q12.
  Lexical's first p13 passage is c1 and lacks those totals despite a gold hit.
- **Segment reconciliation fragmentation:** p19 c4 ends `Margin $ 445` and
  c5 begins `$ 332`; p20 c1 has segment total margin, but consolidated pretax
  income is in c2. Lexical's first p19 hit is c6, an exclusions paragraph,
  rather than the segment results needed for Q14.
- **Margin explanation versus numbers:** p30 c1 has Q15's revenue, expense
  and margin dollars but ends `Total`; c2 starts `Margin % 55% 60%`. The
  exclusions footnote spans c2/c3. Causal statements are c9/c10. Lexical's
  first hit, c10, explains percentage compression but contains neither the
  margin dollars nor the rounded percentage change.
- **Narrative completeness also fails:** lexical Q06 first retrieves p18 c6,
  while recognition timing is in c5/c7; lexical Q13 p17 c4 has rates and
  balances, while the realization condition is in c5. Correct page selection
  is not a sufficient answer-context test.
- **Boilerplate and generic vocabulary:** 41/401 chunks contain `Table of
  Contents`; filing headers repeatedly consume chunk space. Lexical Q11
  selects p6 c1, including a common-stock monetary row, ahead of the scoped
  rounded ATM disclosure. Q01 selects a p9 investments paragraph containing
  repeated dates and balance-sheet vocabulary. This supports investigating
  header/common-term dilution; it does not isolate boilerplate as the cause.
- **Nearby but scoped-out evidence:** lexical Q02 and Q04 favor p35/p36
  liquidity discussion. Those pages discuss related amounts, but do not
  replace the questions' required statement/note evidence. Gold was not
  broadened in response to retrieval errors.

## Verification and limits

Existing application tests: **41 passed**, using deterministic fixtures and
fake providers. No tests were added for this documentation-only change.
Source identity, development schema and gold page validity passed. This is
supplemented by `git diff --check`, a whitespace check on this new untracked
report, and a clean diff for application source and every dataset JSON file.
Captured CLI aggregate output agrees with the detailed metric records. This is
one filing and 15 development questions; differences are descriptive, with
no claim of statistical significance. Page-disjoint splits within the same
document do not establish document independence. The unmeasured holdout
remains narrative-heavy. Human rendered-PDF review and provenance approval
remain pending. No dependencies, application code, retrieval algorithms,
gold labels or holdout files were modified; no commit or push was performed.

## Recommended next steps

1. Complete human review of rendered table headers, units, periods, footnotes
   and publisher provenance. Keep this baseline identified with the current
   draft annotation hash; do not retroactively broaden labels to reward hits.
2. Before selecting a retriever, evaluate returned passage sufficiency on
   development questions, including numerical inputs and explanatory
   components. Keep current flat page metrics and evidence-group diagnostics
   separately named; a page-ranking success must not imply a valid answer.
3. In a separately scoped development experiment, test preserving table rows
   with column headers, units and nearby footnotes, or expanding retrieved
   chunks to the necessary adjacent context. Start with Q01/Q12/Q14/Q15 and
   compare against this unchanged baseline. No such changes were tested here.
4. Investigate generic/common-term matches and repeated filing headers before
   proposing lexical weighting or boilerplate handling. Inspect scoped-out
   duplicate disclosures rather than treating every off-gold hit as useless.
5. Address semantic corpus re-embedding as a separate latency concern, with
   tests proving identical rankings if embeddings are reused. Do not infer
   the cost of a cached index from this per-query re-embedding implementation.
6. Keep the holdout sealed for a separately authorized final comparison;
   broaden to independently labeled filings before generalization claims.
