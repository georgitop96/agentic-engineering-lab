# Oracle FY2027 Q1 Gold Dataset v1 — human acceptance candidate

Milestone 5A is dataset design and evidence review, not a retrieval benchmark.
The questions and annotations are drafts for human approval. No lexical or
semantic retrieval was scored on these questions during their design.
This v1 acceptance candidate is **not human-approved or frozen**. Human
rendered-PDF review and source provenance approval remain pending.

The later [Milestone 5B development baseline](BASELINE.md) records retrieval
diagnostics on Q01–Q15 under the project owner's explicit instruction. It does
not change these gold labels or approval status. The evidence-design and
pre-benchmark verification statements below describe Milestone 5A; the
10-question holdout remains unmeasured.

## Deliverables

| File | Purpose |
| --- | --- |
| [questions.json](questions.json) | All 25 proposed questions, stable IDs and gold PDF pages; accepted by the existing evaluation loader. |
| [development.json](development.json) | Exact projection of Q01–Q15, for later development work after approval. |
| [holdout.json](holdout.json) | Exact projection of Q16–Q25; not scored in this milestone. |
| [annotations.json](annotations.json) | All 25 reference answers, units, periods, arithmetic, evidence passages, minimal sufficient page sets, independent-audit findings and human-review flags. |
| This report | Evidence audit, split rationale, reconciled disagreements and validation results. |

## Source and verification boundary

The source is the local, ignored `data/oracle_fy2027_q1_10q.pdf`, relative to
the [project directory](../..). It is not bundled with this dataset.

- SHA256: `3c9e939c3ac86d28b8047b5308b2fb8dfa6f859ace9ef452f2a2d0f1715474ff`.
- 50 physical PDF pages; source metadata identifies a Form 10-Q filed
  September 11, 2026 for the period ending August 31, 2026.
- The filing describes fiscal 2027 Q1, with comparative quarters ending August
  31, 2026 and 2025. Balance sheet comparisons use August 31 and May 31, 2026.
- Publisher provenance was not independently checked against an external SEC
  filing. Labels apply to these exact local bytes, not a similarly named file.

All gold labels use one-based PDF viewer pages. Printed report page 1 is PDF
page 3, printed page 39 is PDF page 41, and exhibit numbering restarts at PDF
page 42. Do not derive every label by applying a fixed offset to printed pages.

Independent review reads the PDF directly with the installed `pypdf` 6.21.4
in the existing Python 3.12 environment. Exact evidence matching permits only
whitespace normalization; ligatures, punctuation, and numbers remain intact.
Text verification is not a claim of complete visual or publisher verification.
No PDF renderer was available, and no dependency or model was installed.

## Evidence audit report

The independent auditor opened the original local PDF, rather than accepting
the designer's excerpts, and cross-checked numerical tables with both ordinary
and layout extraction. The coordinator separately validates that every stored
excerpt occurs on its labeled page after whitespace normalization and that
every label belongs to the extracted page set. Both methods share `pypdf`, so
their agreement is not an independent rendering-engine check.

The audit distinguishes statement tables in dollars/shares in millions from
narrative billions, and quarter-end balances from three-month flows. Reported
rounded percentages must not be confused with calculations from displayed
amounts or with constant-currency growth. Derived answers must state their
formula and must not be presented as a company-reported adjusted measure.

### Final verification categories

- **Independently source-verified: Q01–Q25.** The evidence auditor's final
  item-level audit supports all current reference answers and gold sets.
  Verification means reading the original local PDF's extracted evidence,
  checking units/periods, cross-checking table layout extraction, and independently
  recalculating derived answers. It does not mean visual inspection.
- **Programmatic-only items: none.** All 77 current stored excerpts also pass
  whitespace-normalized matching against their labeled source pages, but that
  existence check is supplementary and is not the basis for declaring an
  answer correct. Split/projection/schema checks are programmatic checks only.
- **Human review: all 25 remain draft approval candidates.** Rendered-PDF
  checking and external publisher authentication were not performed. High-priority
  interpretation review is flagged for Q02, Q04, Q06, Q07, Q09, Q11, Q12, Q13,
  Q14, Q15, Q18 and Q25. Other table questions still need rendered alignment
  checking even where ordinary and layout extraction agree.
- **Unresolved item-level factual disagreements: none after reconciliation.**
  The two unresolved source interpretations in the exclusion table below were
  not turned into questions or gold answers.

Final Q17/Q19 checks, independently accepted by both auditor and reviewer:

| ID | Physical PDF page | Verified inputs and result |
| --- | --- | --- |
| Q17 | 11 (printed 9) | Level 1 assets 28,289 / total assets in the recurring fair-value table 29,086 × 100 = 97.25985…%, or **97.26%**. Money market funds, **$28,204 million**, are the largest Level 1 component. This denominator is not total company assets. |
| Q19 | 11 (printed 9) | Construction in progress 48,546 − 39,973 = **$8,573 million** increase. Its share of gross PP&E is 48,546 / 153,596 × 100 = 31.60629…%, or **31.61%**. The balance increase is not capital expenditure; the denominator is not net PP&E. |

Reference calculations remain in the annotations. Sensible rounding and
equivalent sign conventions should be accepted in future human answer review;
there is no automated answer grader in the current application.

The initial independent source audit identified these exclusions and cautions:

| Issue | PDF evidence | Disposition |
| --- | --- | --- |
| Commercial-paper repayments | Page 7 shows a dash for net repayments; page 35 describes $1.1 billion used for repayment. | Exclude a reconciliation question: gross versus net might explain the difference, but the relationship is not established by these passages alone. |
| Pretax-income change | Page 35 mentions $318 million in a tax-provision explanation; page 4 reports pretax income of 5,607 versus 3,427 million. | Do not label $318 million as the pretax-income increase; the statement-level arithmetic gives $2,180 million. Human clarification is needed before interpreting the narrative figure. |
| Deferred cloud revenue | Page 13's 6,348 million Cloud row belongs to the current subtotal. | Never label that row as total current-plus-noncurrent cloud deferred revenue. |
| Revenue mix | Pages 23/25/26 describe trailing-four-quarter mix; page 28 describes the current quarter. | Preserve the period and accounting basis in each question and answer. |
| Growth attribution | Pages 28/30 describe contributions to constant-currency growth. | Do not reinterpret contributions as revenue shares or reported-currency growth. |
| Forward-looking claims | Page 37 says full-year capital spending is expected to exceed the preceding fiscal year; controls discussion on page 38 offers reasonable assurance. | Do not invent a numeric spending target or an absolute guarantee against errors/fraud. |

## Label semantics and evaluation limits

`question` and `gold_pages` use the existing evaluation schema. Stable IDs are
additional metadata ignored by the current loader. Reference answers,
calculations, evidence, review flags, and split assignments belong in the
separate annotations rather than application instructions.

`minimal_sufficient_page_sets` in an annotation distinguishes alternatives
from conjunctions: `[[9], [37]]` means either page can suffice; `[[21, 22]]`
means both pages are required. These examples explain the format, not labels
for particular questions. Named notes/statements may deliberately bound the
requested evidence; that scope must be respected during adjudication.

The current evaluator cannot score these logical groups or reference answers.
Hit@1 and MRR reward any labeled page; Recall@2 counts all gold pages, even
alternative sufficient pages, and cannot reach 1 when more than two gold pages
are labeled. Page hits also do not establish row/column, unit, period, footnote,
or passage sufficiency. No scoring algorithm is changed by this proposal.

## Split policy

The proposed split keeps related questions together and has disjoint unions
of labeled PDF pages:

| Split | IDs | Main evidence families |
| --- | --- | --- |
| Development (15) | Q01–Q15 | Liquidity/prepayments/deferred revenue; revenue/segments; leases/commitments/financing; restructuring; tax. |
| Holdout (10) | Q16–Q25 | Fair value and PP&E (Q16/Q17/Q19); legal contingency (Q18); currency illustration (Q20); controls (Q21/Q22); risk disclosure and trading-plan scope (Q23/Q24); bonus-plan ceiling (Q25). |

This is a **page-disjoint, partially overlapping topic holdout**, not complete
evidence-family isolation. Q20 shares currency methodology with development
Q15; Q19 shares the broader asset-investment topic; and Q18's source page 21
also contains financial facts repeated on development pages, although Q18
requires the legal paragraph. These are disclosed exceptions, not hidden
claims of independence. The two table-calculation holdout items both use
page 11, and holdout remains more narrative-heavy than development.

Keep the holdout groups Q16/Q17/Q19, Q21/Q22, and Q23/Q24 intact. Prefer whole
evidence-family groups to a random question split in later revisions. A holdout
inside one public filing is not
document-independent, blind to its designers, or a measure of generalization.
Question wording inevitably reveals some section terminology; difficulty is
a human judgment until assessed on a separately governed benchmark.

Freeze and human-approve the source hash, wording, answers, labels, and split
before retrieval experiments. Use development questions for iteration. Do not
score or tune against the holdout until a separately approved final comparison.
Revising questions after seeing holdout rankings invalidates that holdout.

## Agent contributions and reconciled disagreements

Three specialized, read-only subagents were supported. The coordinator alone
created the repository files; no agent changed application code.

| Role | Contribution |
| --- | --- |
| Dataset designer | Proposed all 25 initial questions, answers, evidence, page sets and 15/10 split. |
| Independent evidence auditor | Independently read the PDF before receiving the draft; audited all 25 final items, units, periods, calculations and sufficient sets; checked both replacements and found source interpretation traps. |
| Evaluation quality reviewer | Reviewed all 25 for ambiguity, leakage and compound tasks; proposed clearer paraphrases; checked current projections and replacements; identified split overlap and type imbalance. |
| Coordinator | Recorded source provenance, validated every excerpt and schema/split invariant, recalculated arithmetic, reconciled findings and assembled the draft. |

| Design disagreement or correction | Final resolution |
| --- | --- |
| Original holdout lacked table calculations. | Replaced Q17's accounting-standard adoption question and Q19's litigation-timeline question with independently audited fair-value and construction-in-progress calculations. Count and split membership stayed unchanged. |
| Quality review suggested “unfinished construction”; the auditor warned that this could imply buildings only. | Q19 uses the precise **construction-in-progress balance**. The continuation footnote describes assets awaiting deployment, so the looser wording was rejected. |
| Section locators made several questions overly lexical, but removing all source scope would make some gold sets incomplete. | Removed numeric note/item locators where practical; retained explicit statement/note scope for Q02 and Q14. Six intentional paraphrases are Q06, Q08, Q15, Q20, Q22 and Q25; this is a qualitative label, not measured retrieval difficulty. |
| The draft reference for Q06 added detail not required by its single-page sufficient path. | General timing is required; extra ratable-recognition and usage-consumption detail is optional, preserving `[[18], [23,24]]`. |
| Q15 mixed a rounded reported margin change with a constant-currency explanation; Q22 retained a stale “No.” after rephrasing. | Qualified Q15's causal explanation explicitly as constant currency and removed Q22's yes/no opening. |
| Human acceptance review found that Q15's stored excerpts omitted support for its margin-dollar increase. | Directly checked physical p30 in ordinary and layout extraction. Added revenue, expense and margin rows, management's margin-growth explanation and the segment exclusions footnote. The reference now explains the $1,667m margin increase alongside the rounded 5-point decline. Question wording, gold page `[30]` and development membership are unchanged. |
| Flat gold labels could conflate alternatives with required multiple pages. | Kept truthful union labels plus separate minimal sufficient sets. Eight mandatory multi-page items are Q02, Q04, Q07, Q09, Q12, Q14, Q18 and Q25. Q03/Q05/Q06/Q11 have alternative sufficient paths. |
| A page-disjoint split was initially stronger-sounding than warranted. | Retained the proposed 15/10 membership, but disclosed topic overlap, shared concepts and the narrative-heavy holdout. Human split approval remains outstanding. |

Q04, Q09, Q13 and Q18 are intentionally compound. Their required answer
components are listed separately in the annotations. A page-ranking hit cannot
demonstrate that all components were recovered. No unresolved factual answer
or gold-label disagreement remains, but these design tradeoffs and the human
review requirements remain visible rather than being presented as settled
production benchmark quality.

## Reproduction prerequisites

Use the existing project environment and the matching local source PDF. Do
not replace it with a different edition or copy without re-auditing labels.
The original 12-question synthetic fixture remains unchanged. These Oracle
files are not automatically loaded into unit tests or CI, because the local
filing is not packaged in the repository.

## Validation results and safe preflight

The coordinator checked 25 unique IDs, the 15/10 exact split projections,
disjoint labeled-page sets, annotation coverage, all minimal sufficient sets,
77 source-matching excerpts, the source hash and all calculation results.
All three question files load through the existing `load_dataset()` and
`validate_gold_pages()` functions. The 41 existing application tests passed;
the new Oracle dataset was not retrieval-scored. `git diff --check` passed.

### v1 acceptance-candidate verification (2026-11-01)

The finalization review used the existing project `.venv` (Python 3.12.16),
without installing dependencies. A one-off read-only consistency check reused
`load_dataset()`, `validate_gold_pages()` and `extract_pdf_pages()` and confirmed:

- Source SHA256 matches the recorded hash; 50 physical PDF pages.
- 25 unique question IDs, 15 development / 10 holdout, exact split projections,
  valid gold pages and disjoint gold-page unions.
- Annotation coverage, sufficient-page-set unions and mandatory-multiple-page
  flags agree; all 77 excerpts match after whitespace normalization only.
- 45 arithmetic checks across 17 items pass at the reference answers' stated
  precision, including Q15's revenue, expense and margin differences.
- All three question files remain byte-identical to the pre-finalization
  snapshot; the other 24 item annotations are unchanged. Only Q15's answer,
  supporting evidence, units, caveat and verification notes changed, together
  with the overall excerpt count and this report. Approval status is unchanged.

Existing application tests passed: `.venv/bin/python -m unittest discover -s
tests -v` from the project directory (41 tests). Repository `git diff --check`
also passed. No retrieval experiment or holdout performance evaluation was run.
These checks do not repeat the full independent agent audit or substitute for
rendered-PDF review or source provenance approval.

Human acceptance must explicitly approve the narrative-heavy holdout (8/10
items carry the narrative tag; only 2/10 carry the table tag) and the fact that
page-disjoint evidence within one filing is not document-independent. Reviewers
must preserve alternative paths versus mandatory combinations: for Q06, p18
alone **or** p23+p24 suffices; for Q02, p3+p7+p8 are **all** required. All 25 items
remain pending human approval, including visual column/unit/period and footnote
checks. Source authenticity/access, wording, answers, labels and split require
human approval before a later freeze; the local PDF remains unbundled.

To check source identity and schema without scoring holdout, run from the
project directory in the existing environment:

```bash
uv run --offline --no-sync python - <<'PY'
from pathlib import Path
import hashlib
from financial_research_copilot.evaluation import load_dataset, validate_gold_pages
from financial_research_copilot.ingestion import extract_pdf_pages

source = Path("data/oracle_fy2027_q1_10q.pdf")
with source.open("rb") as stream:
    assert hashlib.file_digest(stream, "sha256").hexdigest() == "3c9e939c3ac86d28b8047b5308b2fb8dfa6f859ace9ef452f2a2d0f1715474ff"
pages = extract_pdf_pages(source)
root = Path("evals/oracle_fy2027_q1")
for filename, count in (("questions.json", 25), ("development.json", 15), ("holdout.json", 10)):
    questions = load_dataset(root / filename)
    assert len(questions) == count
    validate_gold_pages(questions, (page.page_number for page in pages))
print("Source hash and all three dataset schemas/page labels verified; no retrieval run.")
PY
```

## Recommended next engineering steps

1. Human-review flagged examples against rendered PDF pages, especially units,
   table column alignment, footnotes, and ambiguous narrative interpretations.
2. Approve and freeze the proposed evidence families and split; broaden to
   independently labeled filings before making generalization claims.
3. Run development-only diagnostics to assess table-aware ingestion. Plan
   evidence-group completeness and answer validation separately from current
   page-ranking metrics; do not silently reinterpret the existing scores.
