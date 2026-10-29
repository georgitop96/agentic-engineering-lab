"""Deterministic local chunking and lexical passage retrieval."""

from dataclasses import dataclass
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


class RetrievalError(Exception):
    """A user-actionable search request error."""


def chunk_page_text(page: PageText, max_words: int = 80) -> list[TextChunk]:
    """Split one page into deterministic, non-overlapping word chunks."""

    if max_words < 1:
        raise ValueError("max_words must be greater than zero")

    words = page.text.split()
    return [
        TextChunk(
            document_name=page.document_name,
            page_number=page.page_number,
            chunk_index=chunk_index,
            text=" ".join(words[start : start + max_words]),
        )
        for chunk_index, start in enumerate(range(0, len(words), max_words), start=1)
    ]


def chunk_pages(pages: list[PageText], max_words: int = 80) -> list[TextChunk]:
    """Split all extracted pages into searchable chunks in source order."""

    chunks: list[TextChunk] = []
    for page in pages:
        chunks.extend(chunk_page_text(page, max_words=max_words))
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
