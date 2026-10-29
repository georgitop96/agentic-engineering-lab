"""Explicit manual smoke test for the downloaded local embedding model."""

from pathlib import Path

from financial_research_copilot.ingestion import extract_pdf_pages
from financial_research_copilot.retrieval import chunk_pages, search_chunks
from financial_research_copilot.semantic import FastEmbedder, semantic_search


FIXTURE = Path(__file__).parents[1] / "tests" / "fixtures" / "synthetic_financial_report.pdf"
QUERIES = (
    "What was the company's revenue?",
    "Can the company cover its near-term obligations?",
    "What could interrupt component deliveries?",
)


def main() -> None:
    pages = extract_pdf_pages(FIXTURE)
    chunks = chunk_pages(pages)
    embedder = FastEmbedder()

    for query in QUERIES:
        lexical = search_chunks(chunks, query, limit=1)
        semantic = semantic_search(chunks, query, embedder, limit=1)
        print(f"Query: {query}")
        print(
            "Lexical top page: "
            f"{lexical[0].page_number if lexical else 'none'}"
        )
        print(
            "Semantic top page: "
            f"{semantic[0].page_number if semantic else 'none'} "
            f"(cosine={semantic[0].cosine_similarity:.4f})"
        )
        if semantic:
            print(f"Semantic passage: {semantic[0].text}")
        print()


if __name__ == "__main__":
    main()
