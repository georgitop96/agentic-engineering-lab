"""Local embedding generation and cosine-similarity retrieval."""

from dataclasses import dataclass
import math
from typing import Protocol, Sequence

from .retrieval import TextChunk


DEFAULT_MODEL_NAME = "BAAI/bge-small-en-v1.5"
QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "
Embedding = tuple[float, ...]


class Embedder(Protocol):
    """The small interface required by semantic retrieval."""

    def embed_documents(self, texts: Sequence[str]) -> list[Embedding]:
        """Encode corpus passages with the configured embedding model."""

    def embed_query(self, text: str) -> Embedding:
        """Encode one search query with the same embedding model."""


@dataclass(frozen=True, slots=True)
class SemanticSearchResult:
    """A chunk ranked by cosine similarity, not a calibrated confidence."""

    document_name: str
    page_number: int
    chunk_index: int
    text: str
    cosine_similarity: float


class SemanticSearchError(Exception):
    """A user-actionable semantic search or model-loading error."""


class FastEmbedder:
    """Lazy local adapter for the optional CPU-oriented fastembed dependency."""

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        try:
            from fastembed import TextEmbedding
        except ImportError as error:
            raise SemanticSearchError(
                "Semantic search requires the optional dependency. "
                "Run 'uv sync --extra semantic' first."
            ) from error

        try:
            self._model = TextEmbedding(model_name=model_name)
        except Exception as error:
            raise SemanticSearchError(
                f"Could not load embedding model '{model_name}': {error}"
            ) from error

    def embed_documents(self, texts: Sequence[str]) -> list[Embedding]:
        """Encode passages with the local ONNX model."""

        try:
            vectors = self._model.embed(list(texts))
            return [tuple(float(value) for value in vector) for vector in vectors]
        except Exception as error:
            raise SemanticSearchError(f"Could not embed document chunks: {error}") from error

    def embed_query(self, text: str) -> Embedding:
        """Encode a query with the same local ONNX model."""

        try:
            vectors = list(self._model.embed([QUERY_INSTRUCTION + text]))
            return tuple(float(value) for value in vectors[0])
        except Exception as error:
            raise SemanticSearchError(f"Could not embed search query: {error}") from error


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    """Return cosine similarity for two non-empty, equal-length vectors."""

    if len(left) != len(right) or not left:
        raise ValueError("Embedding vectors must be non-empty and equal in length")

    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise ValueError("Embedding vectors must not have zero magnitude")

    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def semantic_search(
    chunks: list[TextChunk],
    query: str,
    embedder: Embedder,
    limit: int = 5,
) -> list[SemanticSearchResult]:
    """Embed a query and chunks, then rank chunks by cosine similarity."""

    if not query.strip():
        raise SemanticSearchError("Search query must contain at least one word.")
    if limit < 1:
        raise ValueError("limit must be greater than zero")
    if not chunks:
        return []

    document_embeddings = embedder.embed_documents([chunk.text for chunk in chunks])
    if len(document_embeddings) != len(chunks):
        raise SemanticSearchError(
            "Embedding model returned a different number of document vectors."
        )
    query_embedding = embedder.embed_query(query)

    results = [
        SemanticSearchResult(
            document_name=chunk.document_name,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            text=chunk.text,
            cosine_similarity=cosine_similarity(query_embedding, document_embedding),
        )
        for chunk, document_embedding in zip(chunks, document_embeddings)
    ]
    results.sort(
        key=lambda result: (
            -result.cosine_similarity,
            result.document_name,
            result.page_number,
            result.chunk_index,
        )
    )
    return results[:limit]
