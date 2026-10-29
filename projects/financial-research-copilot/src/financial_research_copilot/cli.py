"""Command-line entry point for the Financial Research Copilot scaffold."""

import argparse

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without performing I/O or external calls."""

    parser = argparse.ArgumentParser(
        prog="frc",
        description="Research public financial reports with source evidence.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main() -> int:
    """Parse the scaffold CLI and report the current implementation status."""

    build_parser().parse_args()
    print("Financial Research Copilot: ingestion and retrieval are planned.")
    return 0
