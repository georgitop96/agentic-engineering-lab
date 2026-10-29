"""Command-line entry point for the Financial Research Copilot."""

import argparse
from pathlib import Path

from . import __version__
from .ingestion import PDFIngestionError, extract_pdf_pages


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
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    args = build_parser().parse_args(argv)
    if args.command != "ingest":
        build_parser().print_help()
        return 0

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
