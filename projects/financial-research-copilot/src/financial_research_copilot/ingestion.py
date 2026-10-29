"""Local PDF ingestion with page-level metadata."""

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


@dataclass(frozen=True, slots=True)
class PageText:
    """Text extracted from one PDF page."""

    document_name: str
    page_number: int
    text: str


class PDFIngestionError(Exception):
    """A user-actionable error while opening or extracting a PDF."""


def extract_pdf_pages(pdf_path: str | Path) -> list[PageText]:
    """Extract text from every page of a local PDF, preserving page numbers.

    Page numbers are one-based to match the convention used by PDF viewers.
    """

    path = Path(pdf_path)
    if not path.exists():
        raise PDFIngestionError(f"PDF file does not exist: {path}")
    if not path.is_file():
        raise PDFIngestionError(f"PDF path is not a regular file: {path}")

    try:
        reader = PdfReader(str(path))
        pages = [
            PageText(
                document_name=path.name,
                page_number=page_number,
                text=page.extract_text() or "",
            )
            for page_number, page in enumerate(reader.pages, start=1)
        ]
    except (OSError, PdfReadError, ValueError, TypeError) as error:
        raise PDFIngestionError(f"Could not read PDF '{path}': {error}") from error

    return pages
