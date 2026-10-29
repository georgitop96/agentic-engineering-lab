"""Command-line entry point for the Financial Research Copilot."""

import argparse
from pathlib import Path

from . import __version__
from .ingestion import PDFIngestionError, extract_pdf_pages
from .retrieval import RetrievalError, chunk_pages, search_chunks


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

    try:
        pages = extract_pdf_pages(args.pdf_path)
        results = search_chunks(chunk_pages(pages), args.query)
    except (PDFIngestionError, RetrievalError) as error:
        print(f"Error: {error}")
        return 2

    if not results:
        print("No matches found.")
        return 0

    for rank, result in enumerate(results, start=1):
        print(f"Result {rank}:")
        print(f"Document: {result.document_name}")
        print(f"Page: {result.page_number}")
        print(f"Score: {result.score:.2f}")
        print(f"Passage: {result.text}")
        if rank != len(results):
            print()
    return 0
