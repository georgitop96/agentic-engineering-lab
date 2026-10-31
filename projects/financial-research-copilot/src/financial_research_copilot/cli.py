"""Command-line entry point for the Financial Research Copilot."""

import argparse
from pathlib import Path

from . import __version__
from .evaluation import EvaluationDataError, evaluate, load_dataset, validate_gold_pages
from .ingestion import PDFIngestionError, extract_pdf_pages
from .retrieval import RetrievalError, chunk_pages, search_chunks
from .semantic import (
    FastEmbedder,
    SemanticSearchError,
    semantic_search,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without performing I/O or external calls."""

    parser = argparse.ArgumentParser(
        prog="frc",
        description="Research public financial reports with source evidence.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command")

    ingest_parser = subparsers.add_parser(
        "ingest", help="extract page-aware text from a local PDF"
    )
    ingest_parser.add_argument("pdf_path", type=Path, help="path to a local PDF")

    search_parser = subparsers.add_parser(
        "search", help="search passages in a local PDF"
    )
    search_parser.add_argument("pdf_path", type=Path, help="path to a local PDF")
    search_parser.add_argument("query", help="search terms")
    search_parser.add_argument(
        "--method",
        choices=("lexical", "semantic"),
        default="lexical",
        help="retrieval method (default: lexical)",
    )

    chunks_parser = subparsers.add_parser(
        "chunks", help="inspect page-aware PDF chunks"
    )
    chunks_parser.add_argument("pdf_path", type=Path, help="path to a local PDF")
    chunks_parser.add_argument(
        "--chunk-size",
        type=int,
        default=80,
        help="maximum words per chunk (default: 80)",
    )
    chunks_parser.add_argument(
        "--sentence-overlap",
        type=int,
        default=0,
        help="complete sentences repeated between chunks (default: 0)",
    )

    eval_parser = subparsers.add_parser(
        "eval", help="evaluate ranked pages against a labeled JSON dataset"
    )
    eval_parser.add_argument("pdf_path", type=Path, help="path to a local PDF")
    eval_parser.add_argument(
        "--method",
        choices=("lexical", "semantic"),
        default="lexical",
        help="retrieval method (default: lexical)",
    )
    eval_parser.add_argument(
        "--dataset",
        required=True,
        type=Path,
        help="path to a labeled JSON dataset",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    args = build_parser().parse_args(argv)
    if args.command is None:
        build_parser().print_help()
        return 0

    if args.command == "ingest":
        try:
            pages = extract_pdf_pages(args.pdf_path)
        except PDFIngestionError as error:
            print(f"Error: {error}")
            return 2

        print(f"Document: {args.pdf_path.name}")
        print(f"Pages: {len(pages)}")
        for page in pages:
            print(f"\n--- Page {page.page_number} ---")
            print(page.text.strip())
        return 0

    if args.command == "chunks":
        try:
            pages = extract_pdf_pages(args.pdf_path)
            chunks = chunk_pages(
                pages,
                max_words=args.chunk_size,
                sentence_overlap=args.sentence_overlap,
            )
        except (PDFIngestionError, ValueError) as error:
            print(f"Error: {error}")
            return 2

        for chunk_number, chunk in enumerate(chunks, start=1):
            print(f"Chunk {chunk_number}:")
            print(f"Document: {chunk.document_name}")
            print(f"Page: {chunk.page_number}")
            print(f"Chunk index: {chunk.chunk_index}")
            print(f"Word count: {len(chunk.text.split())}")
            print(f"Text: {chunk.text}")
            if chunk_number != len(chunks):
                print()
        return 0

    if args.command == "eval":
        try:
            questions = load_dataset(args.dataset)
            pages = extract_pdf_pages(args.pdf_path)
            chunks = chunk_pages(pages)
            if not chunks:
                raise PDFIngestionError(
                    "Evaluation requires extractable text; this PDF produced no "
                    "chunks. Use a PDF with a text layer (OCR is not implemented)."
                )
            validate_gold_pages(questions, (page.page_number for page in pages))
            if args.method == "semantic":
                embedder = FastEmbedder()
                retrieve = lambda question: semantic_search(
                    chunks, question, embedder, limit=len(chunks)
                )
            else:
                retrieve = lambda question: search_chunks(
                    chunks, question, limit=len(chunks)
                )
            metrics = evaluate(questions, retrieve)
        except (
            PDFIngestionError,
            EvaluationDataError,
            RetrievalError,
            SemanticSearchError,
            ValueError,
        ) as error:
            print(f"Error: {error}")
            return 2

        print("Question | Retrieved pages | Gold pages | Hit@1 | Recall@2 | MRR")
        for question in metrics.questions:
            print(
                f"{question.question} | "
                f"{','.join(map(str, question.retrieved_pages)) or '-'} | "
                f"{','.join(map(str, question.gold_pages))} | "
                f"{question.hit_at_1:.2f} | {question.recall_at_2:.2f} | "
                f"{question.mean_reciprocal_rank:.2f}"
            )
        print(
            f"Average | - | - | {metrics.hit_at_1:.3f} | "
            f"{metrics.recall_at_2:.3f} | {metrics.mean_reciprocal_rank:.3f}"
        )
        return 0

    try:
        pages = extract_pdf_pages(args.pdf_path)
        chunks = chunk_pages(pages)
        if args.method == "semantic":
            results = semantic_search(
                chunks,
                args.query,
                FastEmbedder(),
            )
        else:
            results = search_chunks(chunks, args.query)
    except (PDFIngestionError, RetrievalError, SemanticSearchError) as error:
        print(f"Error: {error}")
        return 2

    if not results:
        print("No matches found.")
        return 0

    for rank, result in enumerate(results, start=1):
        print(f"Result {rank}:")
        print(f"Document: {result.document_name}")
        print(f"Page: {result.page_number}")
        if args.method == "semantic":
            print(f"Cosine similarity: {result.cosine_similarity:.4f}")
        else:
            print(f"Score: {result.score:.2f}")
        print(f"Passage: {result.text}")
        if rank != len(results):
            print()
    return 0
