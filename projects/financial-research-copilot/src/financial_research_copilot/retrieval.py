"""Deterministic local chunking and lexical passage retrieval."""

from dataclasses import dataclass
from functools import lru_cache
import re

from .ingestion import PageText


@dataclass(frozen=True, slots=True)
class TextChunk:
    """A searchable word chunk retaining its source page metadata."""

    document_name: str
    page_number: int
    chunk_index: int
    text: str


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A ranked chunk returned by lexical search."""

    document_name: str
    page_number: int
    chunk_index: int
    text: str
    score: float


@dataclass(frozen=True, slots=True)
class _ChunkDraft:
    """Internal chunk state used while preserving complete sentences."""

    text: str
    complete_sentences: tuple[str, ...]


class RetrievalError(Exception):
    """A user-actionable search request error."""


_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def _split_sentences(text: str) -> list[str]:
    """Split extracted page text at conservative sentence boundaries."""

    return [sentence.strip() for sentence in _SENTENCE_BOUNDARY.split(text.strip()) if sentence.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


def _partition_sentences(
    sentences: list[str], max_words: int
) -> list[_ChunkDraft]:
    """Partition sentences into balanced groups using the fewest chunks."""

    if not sentences:
        return []
    sentence_tuple = tuple(sentences)
    word_counts = tuple(_word_count(sentence) for sentence in sentence_tuple)
    total_words = sum(word_counts)
    minimum_groups = (total_words + max_words - 1) // max_words
    prefix_words = [0]
    for count in word_counts:
        prefix_words.append(prefix_words[-1] + count)

    for group_count in range(minimum_groups, len(sentences) + 1):
        target_words = total_words / group_count

        @lru_cache(maxsize=None)
        def solve(
            start: int, groups_left: int
        ) -> tuple[float, tuple[tuple[str, ...], ...]] | None:
            if groups_left == 1:
                if start >= len(sentence_tuple):
                    return None
                group_words = prefix_words[-1] - prefix_words[start]
                if group_words > max_words:
                    return None
                return (
                    (group_words - target_words) ** 2,
                    (sentence_tuple[start:],),
                )

            best: tuple[float, tuple[tuple[str, ...], ...]] | None = None
            for end in range(start + 1, len(sentence_tuple)):
                group_words = prefix_words[end] - prefix_words[start]
                if group_words > max_words:
                    break
                remaining_words = prefix_words[-1] - prefix_words[end]
                remaining_sentences = len(sentence_tuple) - end
                if remaining_words > (groups_left - 1) * max_words:
                    continue
                if remaining_sentences < groups_left - 1:
                    continue
                tail = solve(end, groups_left - 1)
                if tail is None:
                    continue
                candidate = (
                    (group_words - target_words) ** 2 + tail[0],
                    (sentence_tuple[start:end],) + tail[1],
                )
                if best is None or candidate[0] < best[0]:
                    best = candidate
            return best

        solution = solve(0, group_count)
        if solution is not None:
            return [
                _ChunkDraft(text=" ".join(group), complete_sentences=group)
                for group in solution[1]
            ]

    raise AssertionError("Could not partition sentences")


def _merge_fitting_drafts(
    drafts: list[_ChunkDraft], max_words: int
) -> list[_ChunkDraft]:
    """Merge adjacent drafts when their combined text fits the limit."""

    merged: list[_ChunkDraft] = []
    for draft in drafts:
        if merged and _word_count(merged[-1].text) + _word_count(draft.text) <= max_words:
            previous = merged[-1]
            merged[-1] = _ChunkDraft(
                text=f"{previous.text} {draft.text}",
                complete_sentences=(
                    previous.complete_sentences + draft.complete_sentences
                ),
            )
        else:
            merged.append(draft)
    return merged


def _partition_with_overlap(
    sentences: list[str], max_words: int, overlap_sentences: int
) -> list[_ChunkDraft]:
    """Build sentence windows that repeat complete sentences at boundaries."""

    drafts: list[_ChunkDraft] = []
    start = 0
    while start < len(sentences):
        end = start
        current_words = 0
        while end < len(sentences):
            sentence_words = _word_count(sentences[end])
            if current_words and current_words + sentence_words > max_words:
                break
            current_words += sentence_words
            end += 1
        drafts.append(
            _ChunkDraft(
                text=" ".join(sentences[start:end]),
                complete_sentences=tuple(sentences[start:end]),
            )
        )
        if end == len(sentences):
            break
        start = max(start + 1, end - overlap_sentences)
    return drafts


def chunk_page_text(
    page: PageText,
    max_words: int = 80,
    sentence_overlap: int = 0,
) -> list[TextChunk]:
    """Split one page into sentence-aware, deterministic word-bounded chunks.

    Complete sentences are kept together when they fit. Sentences longer than
    ``max_words`` are deterministically split into word windows as a fallback.
    ``sentence_overlap`` optionally repeats complete sentences between chunks.
    """

    if max_words < 1:
        raise ValueError("max_words must be greater than zero")
    if sentence_overlap < 0:
        raise ValueError("sentence_overlap must not be negative")

    sentences = _split_sentences(page.text)
    if sentence_overlap and all(
        len(sentence.split()) <= max_words for sentence in sentences
    ):
        drafts = _partition_with_overlap(sentences, max_words, sentence_overlap)
        texts = [draft.text for draft in drafts]
    else:
        drafts = []
        complete_sentence_run: list[str] = []
        for sentence in sentences:
            words = sentence.split()
            if len(words) > max_words:
                drafts.extend(_partition_sentences(complete_sentence_run, max_words))
                complete_sentence_run = []
                for start in range(0, len(words), max_words):
                    drafts.append(
                        _ChunkDraft(
                            text=" ".join(words[start : start + max_words]),
                            complete_sentences=(),
                        )
                    )
                continue
            complete_sentence_run.append(sentence)

        drafts.extend(_partition_sentences(complete_sentence_run, max_words))
        drafts = _merge_fitting_drafts(drafts, max_words)
        texts = [draft.text for draft in drafts]
    return [
        TextChunk(
            document_name=page.document_name,
            page_number=page.page_number,
            chunk_index=chunk_index,
            text=text,
        )
        for chunk_index, text in enumerate(texts, start=1)
    ]


def chunk_pages(
    pages: list[PageText], max_words: int = 80, sentence_overlap: int = 0
) -> list[TextChunk]:
    """Split all extracted pages into searchable chunks in source order."""

    chunks: list[TextChunk] = []
    for page in pages:
        chunks.extend(
            chunk_page_text(
                page,
                max_words=max_words,
                sentence_overlap=sentence_overlap,
            )
        )
    return chunks


def _terms(text: str) -> list[str]:
    """Return case-insensitive word-like terms for lexical matching."""

    return re.findall(r"\b[\w']+\b", text.casefold())


def search_chunks(
    chunks: list[TextChunk], query: str, limit: int = 5
) -> list[SearchResult]:
    """Rank chunks by query-term coverage and return up to ``limit`` results."""

    query_terms = set(_terms(query))
    if not query_terms:
        raise RetrievalError("Search query must contain at least one word.")
    if limit < 1:
        raise ValueError("limit must be greater than zero")

    results: list[SearchResult] = []
    for chunk in chunks:
        chunk_terms = set(_terms(chunk.text))
        matched_terms = query_terms & chunk_terms
        if not matched_terms:
            continue
        score = len(matched_terms) / len(query_terms)
        results.append(
            SearchResult(
                document_name=chunk.document_name,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                score=score,
            )
        )

    results.sort(
        key=lambda result: (
            -result.score,
            result.document_name,
            result.page_number,
            result.chunk_index,
        )
    )
    return results[:limit]
