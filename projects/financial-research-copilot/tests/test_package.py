import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from financial_research_copilot import __version__
from financial_research_copilot.cli import build_parser, main
from financial_research_copilot.ingestion import PDFIngestionError, extract_pdf_pages
from financial_research_copilot.retrieval import (
    RetrievalError,
    TextChunk,
    chunk_page_text,
    chunk_pages,
    search_chunks,
)


FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_report.pdf"


class PackageTests(unittest.TestCase):
    def test_package_has_version(self) -> None:
        self.assertEqual(__version__, "0.1.0")

    def test_cli_parser_has_expected_program_name(self) -> None:
        self.assertEqual(build_parser().prog, "frc")

    def test_extracts_each_page_with_document_name_and_one_based_number(self) -> None:
        pages = extract_pdf_pages(FIXTURE)

        self.assertEqual([page.page_number for page in pages], [1, 2])
        self.assertEqual([page.document_name for page in pages], ["synthetic_report.pdf"] * 2)
        self.assertIn("Revenue increased in 2025.", pages[0].text)
        self.assertIn("Supplier concentration is a risk.", pages[1].text)

    def test_missing_path_is_reported_as_ingestion_error(self) -> None:
        with self.assertRaisesRegex(PDFIngestionError, "does not exist"):
            extract_pdf_pages("missing-report.pdf")

    def test_directory_path_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(PDFIngestionError, "regular file"):
                extract_pdf_pages(directory)

    def test_invalid_pdf_is_reported_as_ingestion_error(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.pdf"
            path.write_text("not a PDF", encoding="utf-8")
            with self.assertRaises(PDFIngestionError):
                extract_pdf_pages(path)

    def test_unreadable_pdf_is_reported_as_ingestion_error(self) -> None:
        with patch(
            "financial_research_copilot.ingestion.PdfReader",
            side_effect=OSError("permission denied"),
        ):
            with self.assertRaisesRegex(PDFIngestionError, "Could not read PDF"):
                extract_pdf_pages(FIXTURE)

    def test_cli_ingest_prints_page_aware_output(self) -> None:
        with patch("builtins.print") as print_mock:
            exit_code = main(["ingest", str(FIXTURE)])

        self.assertEqual(exit_code, 0)
        output = "\n".join(call.args[0] for call in print_mock.call_args_list)
        self.assertIn("Document: synthetic_report.pdf", output)
        self.assertIn("--- Page 1 ---", output)
        self.assertIn("--- Page 2 ---", output)

    def test_cli_reports_invalid_path_without_traceback(self) -> None:
        with patch("builtins.print") as print_mock:
            exit_code = main(["ingest", "missing-report.pdf"])

        self.assertEqual(exit_code, 2)
        self.assertIn("Error: PDF file does not exist", print_mock.call_args.args[0])

    def test_chunks_preserve_page_metadata_and_are_deterministic(self) -> None:
        pages = extract_pdf_pages(FIXTURE)

        chunks = chunk_pages(pages, max_words=3)

        self.assertEqual(
            chunks,
            [
                TextChunk("synthetic_report.pdf", 1, 1, "Revenue increased in"),
                TextChunk("synthetic_report.pdf", 1, 2, "2025."),
                TextChunk("synthetic_report.pdf", 2, 1, "Supplier concentration is"),
                TextChunk("synthetic_report.pdf", 2, 2, "a risk."),
            ],
        )
        self.assertEqual(chunk_page_text(pages[0], max_words=3), chunks[:2])

    def test_search_ranks_by_query_term_coverage(self) -> None:
        chunks = [
            TextChunk("report.pdf", 1, 1, "supplier concentration"),
            TextChunk("report.pdf", 2, 1, "supplier concentration is a risk"),
            TextChunk("report.pdf", 3, 1, "risk only"),
        ]

        results = search_chunks(chunks, "supplier risk")

        self.assertEqual([result.page_number for result in results], [2, 1, 3])
        self.assertEqual([result.score for result in results], [1.0, 0.5, 0.5])

    def test_search_returns_no_matches(self) -> None:
        pages = extract_pdf_pages(FIXTURE)

        self.assertEqual(search_chunks(chunk_pages(pages), "quarterly earnings"), [])

    def test_search_rejects_empty_query(self) -> None:
        with self.assertRaisesRegex(RetrievalError, "at least one word"):
            search_chunks([], "   ")

    def test_cli_search_prints_ranked_result(self) -> None:
        with patch("builtins.print") as print_mock:
            exit_code = main(["search", str(FIXTURE), "supplier risk"])

        self.assertEqual(exit_code, 0)
        output = "\n".join(call.args[0] for call in print_mock.call_args_list)
        self.assertEqual(
            output,
            "\n".join(
                [
                    "Result 1:",
                    "Document: synthetic_report.pdf",
                    "Page: 2",
                    "Score: 1.00",
                    "Passage: Supplier concentration is a risk.",
                ]
            ),
        )

    def test_cli_search_handles_no_matches_and_empty_query(self) -> None:
        with patch("builtins.print") as print_mock:
            no_match_exit_code = main(
                ["search", str(FIXTURE), "quarterly earnings"]
            )
        self.assertEqual(no_match_exit_code, 0)
        self.assertEqual(print_mock.call_args.args[0], "No matches found.")

        with patch("builtins.print") as print_mock:
            empty_query_exit_code = main(["search", str(FIXTURE), " "])
        self.assertEqual(empty_query_exit_code, 2)
        self.assertIn("at least one word", print_mock.call_args.args[0])

    def test_cli_search_handles_invalid_file(self) -> None:
        with patch("builtins.print") as print_mock:
            exit_code = main(["search", "missing-report.pdf", "risk"])

        self.assertEqual(exit_code, 2)
        self.assertIn("Error: PDF file does not exist", print_mock.call_args.args[0])
