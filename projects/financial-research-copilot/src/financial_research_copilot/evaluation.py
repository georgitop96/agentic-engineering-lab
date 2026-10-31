"""Small, page-level retrieval evaluation utilities."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Callable, Iterable, Sequence


class EvaluationDataError(ValueError):
    """An evaluation dataset is missing or contains invalid data."""


@dataclass(frozen=True, slots=True)
class EvaluationQuestion:
    """One question and its manually labeled relevant one-based pages."""

    question: str
    gold_pages: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class QuestionMetrics:
    """Page-ranking metrics for one evaluation question."""

    question: str
    retrieved_pages: tuple[int, ...]
    gold_pages: tuple[int, ...]
    hit_at_1: float
    recall_at_2: float
    mean_reciprocal_rank: float


@dataclass(frozen=True, slots=True)
class EvaluationMetrics:
    """Per-question results and their macro averages."""

    questions: tuple[QuestionMetrics, ...]

    @property
    def hit_at_1(self) -> float:
        return _average(question.hit_at_1 for question in self.questions)

    @property
    def recall_at_2(self) -> float:
        return _average(question.recall_at_2 for question in self.questions)

    @property
    def mean_reciprocal_rank(self) -> float:
        return _average(
            question.mean_reciprocal_rank for question in self.questions
        )


def load_dataset(path: str | Path) -> list[EvaluationQuestion]:
    """Load and validate a JSON list of evaluation questions."""

    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise EvaluationDataError(f"Evaluation dataset does not exist: {path}") from error
    except OSError as error:
        raise EvaluationDataError(f"Could not read evaluation dataset: {error}") from error
    except json.JSONDecodeError as error:
        raise EvaluationDataError(f"Evaluation dataset is not valid JSON: {error}") from error

    if not isinstance(data, list) or not data:
        raise EvaluationDataError("Evaluation dataset must be a non-empty JSON list.")

    questions: list[EvaluationQuestion] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise EvaluationDataError(f"Question {index} must be a JSON object.")
        question = item.get("question")
        gold_pages = item.get("gold_pages")
        if not isinstance(question, str) or not question.strip():
            raise EvaluationDataError(
                f"Question {index} needs a non-empty 'question'."
            )
        if (
            not isinstance(gold_pages, list)
            or not gold_pages
            or any(
                isinstance(page, bool) or not isinstance(page, int) or page < 1
                for page in gold_pages
            )
            or len(set(gold_pages)) != len(gold_pages)
        ):
            raise EvaluationDataError(
                f"Question {index} needs unique positive integer 'gold_pages'."
            )
        questions.append(EvaluationQuestion(question.strip(), tuple(gold_pages)))
    return questions


def validate_gold_pages(
    questions: Sequence[EvaluationQuestion], page_numbers: Iterable[int]
) -> None:
    """Reject labels absent from the extracted document's actual page set."""

    available = set(page_numbers)
    for index, question in enumerate(questions, start=1):
        missing = set(question.gold_pages) - available
        if missing:
            raise EvaluationDataError(
                f"Question {index} ({question.question!r}) labels pages "
                f"{sorted(missing)} absent from this PDF. "
                f"Extracted pages: {sorted(available)}. "
                "Correct 'gold_pages' or select the matching PDF."
            )


def unique_pages(results: Sequence[object]) -> tuple[int, ...]:
    """Deduplicate ranked chunks by page, preserving first-seen rank order."""

    pages: list[int] = []
    seen: set[int] = set()
    for result in results:
        page = getattr(result, "page_number", None)
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            raise EvaluationDataError(
                "Retriever results must have positive page_number values."
            )
        if page not in seen:
            seen.add(page)
            pages.append(page)
    return tuple(pages)


def score_question(question: EvaluationQuestion, results: Sequence[object]) -> QuestionMetrics:
    """Score one question using unique page ranks.

    Hit@1 is one when the first retrieved page is relevant, otherwise zero.
    Recall@2 is relevant pages in the first two unique pages divided by the
    number of gold pages. MRR is the reciprocal of the first relevant page's
    one-based rank. All metrics are zero when no retrieved page is relevant
    (including an empty result list).
    """

    retrieved = unique_pages(results)
    gold = set(question.gold_pages)
    first_rank = next(
        (rank for rank, page in enumerate(retrieved, start=1) if page in gold),
        None,
    )
    return QuestionMetrics(
        question=question.question,
        retrieved_pages=retrieved,
        gold_pages=question.gold_pages,
        hit_at_1=float(bool(retrieved and retrieved[0] in gold)),
        recall_at_2=len(set(retrieved[:2]) & gold) / len(gold),
        mean_reciprocal_rank=0.0 if first_rank is None else 1.0 / first_rank,
    )


def evaluate(
    questions: Sequence[EvaluationQuestion],
    retrieve: Callable[[str], Sequence[object]],
) -> EvaluationMetrics:
    """Retrieve and macro-average a labeled question set."""

    return EvaluationMetrics(
        tuple(
            score_question(question, retrieve(question.question))
            for question in questions
        )
    )


def _average(values: Iterable[float]) -> float:
    values = tuple(values)
    return sum(values) / len(values) if values else 0.0
