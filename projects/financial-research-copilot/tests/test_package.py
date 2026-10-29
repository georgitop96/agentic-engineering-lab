import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from financial_research_copilot import __version__
from financial_research_copilot.cli import build_parser, main
from financial_research_copilot.ingestion import (
    PDFIngestionError,
    PageText,
    extract_pdf_pages,
)
from financial_research_copilot.retrieval import (
    RetrievalError,
    TextChunk,
    chunk_page_text,
    chunk_pages,
    search_chunks,
)
from financial_research_copilot.semantic import (
    SemanticSearchError,
    cosine_similarity,
    semantic_search,
)


FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_report.pdf"
FINANCIAL_FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_financial_report.pdf"


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
        output = "\n".join(
            call.args[0] if call.args else "" for call in print_mock.call_args_list
        )
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

    def test_semantic_search_ranks_fake_embeddings_by_cosine_similarity(self) -> None:
        chunks = [
            TextChunk("report.pdf", 1, 1, "revenue growth"),
            TextChunk("report.pdf", 2, 1, "cash liquidity"),
        ]

        class FakeEmbedder:
            def __init__(self) -> None:
                self.document_texts: list[str] = []
                self.query_text = ""

            def embed_documents(self, texts: list[str]) -> list[tuple[float, ...]]:
                self.document_texts = texts
                return [(1.0, 0.0), (0.0, 1.0)]

            def embed_query(self, text: str) -> tuple[float, ...]:
                self.query_text = text
                return (0.0, 1.0)

        embedder = FakeEmbedder()
        results = semantic_search(chunks, "Can the company cover bills?", embedder)

        self.assertEqual(embedder.document_texts, [chunk.text for chunk in chunks])
        self.assertEqual(embedder.query_text, "Can the company cover bills?")
        self.assertEqual([result.page_number for result in results], [2, 1])
        self.assertEqual(results[0].cosine_similarity, 1.0)
        self.assertEqual(results[1].cosine_similarity, 0.0)

    def test_cosine_similarity_is_not_a_confidence_score(self) -> None:
        self.assertAlmostEqual(cosine_similarity((1.0, 1.0), (1.0, 0.0)), 0.707106, places=5)

    def test_semantic_search_rejects_empty_query(self) -> None:
        with self.assertRaisesRegex(SemanticSearchError, "at least one word"):
            semantic_search([], "   ", object())

    def test_semantic_search_rejects_wrong_embedding_count(self) -> None:
        class BrokenEmbedder:
            def embed_documents(self, texts: list[str]) -> list[tuple[float, ...]]:
                return []

            def embed_query(self, text: str) -> tuple[float, ...]:
                return (1.0,)

        chunks = [TextChunk("report.pdf", 1, 1, "revenue")]
        with self.assertRaisesRegex(SemanticSearchError, "different number"):
            semantic_search(chunks, "sales", BrokenEmbedder())

    def test_cli_parser_accepts_semantic_method(self) -> None:
        args = build_parser().parse_args(
            ["search", "report.pdf", "cash flow", "--method", "semantic"]
        )

        self.assertEqual(args.method, "semantic")

    def test_financial_fixture_has_multiple_sections_and_more_than_240_words(self) -> None:
        pages = extract_pdf_pages(FINANCIAL_FIXTURE)
        text = " ".join(page.text for page in pages)

        self.assertEqual(len(pages), 4)
        self.assertGreater(len(text.split()), 240)
        for section in ("Revenue", "Liquidity", "Debt", "Supplier risk"):
            self.assertIn(section, text)

    def test_chunk_sizes_preserve_text_and_respect_limits(self) -> None:
        pages = extract_pdf_pages(FINANCIAL_FIXTURE)
        expected_page_words = [page.text.split() for page in pages]

        for chunk_size, expected_counts in (
            (40, [3, 3, 3, 3]),
            (80, [1, 2, 2, 2]),
            (120, [1, 1, 1, 1]),
        ):
            chunks = chunk_pages(pages, max_words=chunk_size)
            self.assertEqual(
                [
                    sum(
                        1
                        for chunk in chunks
                        if chunk.page_number == page_number
                    )
                    for page_number in range(1, len(pages) + 1)
                ],
                expected_counts,
            )

            for page_number, page_words in enumerate(expected_page_words, start=1):
                page_chunks = [
                    chunk for chunk in chunks if chunk.page_number == page_number
                ]
                self.assertEqual(
                    [chunk.chunk_index for chunk in page_chunks],
                    list(range(1, len(page_chunks) + 1)),
                )
                self.assertTrue(
                    all(len(chunk.text.split()) <= chunk_size for chunk in page_chunks)
                )
                self.assertEqual(
                    " ".join(chunk.text for chunk in page_chunks).split(),
                    page_words,
                )

            self.assertEqual(
                [chunk.page_number for chunk in chunks],
                sorted(chunk.page_number for chunk in chunks),
            )

    def test_sentence_aware_chunks_keep_complete_sentences_and_order(self) -> None:
        page = PageText(
            document_name="sentences.pdf",
            page_number=3,
            text="Revenue rose. Cash increased. Debt fell. Supplier risk remained.",
        )

        chunks = chunk_page_text(page, max_words=5)

        self.assertEqual(
            [chunk.text for chunk in chunks],
            [
                "Revenue rose. Cash increased.",
                "Debt fell. Supplier risk remained.",
            ],
        )
        self.assertEqual([chunk.page_number for chunk in chunks], [3, 3])
        self.assertEqual([chunk.chunk_index for chunk in chunks], [1, 2])
        self.assertTrue(all(chunk.text.endswith(".") for chunk in chunks))

    def test_oversized_sentence_uses_deterministic_word_fallback_and_merges_tail(self) -> None:
        page = PageText(
            document_name="long-sentence.pdf",
            page_number=1,
            text=(
                "One two three four five six seven eight nine ten. "
                "Next sentence follows."
            ),
        )

        chunks = chunk_page_text(page, max_words=8)

        self.assertEqual(
            [chunk.text for chunk in chunks],
            [
                "One two three four five six seven eight",
                "nine ten. Next sentence follows.",
            ],
        )
        self.assertTrue(all(len(chunk.text.split()) <= 8 for chunk in chunks))
        self.assertEqual(
            " ".join(chunk.text for chunk in chunks).split(),
            page.text.split(),
        )

    def test_sentence_overlap_is_opt_in_and_stays_on_one_page(self) -> None:
        page = PageText(
            document_name="overlap.pdf",
            page_number=2,
            text="Revenue rose. Cash increased. Debt fell. Supplier risk remained.",
        )

        without_overlap = chunk_page_text(page, max_words=5)
        with_overlap = chunk_page_text(page, max_words=5, sentence_overlap=1)

        self.assertEqual(
            [chunk.text for chunk in without_overlap],
            ["Revenue rose. Cash increased.", "Debt fell. Supplier risk remained."],
        )
        self.assertGreaterEqual(len(with_overlap), len(without_overlap))
        self.assertTrue(all(len(chunk.text.split()) <= 5 for chunk in with_overlap))
        self.assertEqual(
            [chunk.page_number for chunk in with_overlap],
            [2, 2, 2],
        )

    def test_cli_chunks_displays_metadata_and_word_count(self) -> None:
        with patch("builtins.print") as print_mock:
            exit_code = main(
                ["chunks", str(FINANCIAL_FIXTURE), "--chunk-size", "120"]
            )

        self.assertEqual(exit_code, 0)
        output = "\n".join(
            call.args[0] if call.args else "" for call in print_mock.call_args_list
        )
        self.assertIn("Chunk 1:", output)
        self.assertIn("Document: synthetic_financial_report.pdf", output)
        self.assertIn("Page: 1", output)
        self.assertIn("Chunk index: 1", output)
        self.assertIn("Word count: 77", output)
        self.assertIn("Text: Asteron Ledger is a fictional manufacturer", output)

    def test_cli_chunks_rejects_invalid_chunk_size(self) -> None:
        with patch("builtins.print") as print_mock:
            exit_code = main(
                ["chunks", str(FINANCIAL_FIXTURE), "--chunk-size", "0"]
            )

        self.assertEqual(exit_code, 2)
        self.assertIn("max_words must be greater than zero", print_mock.call_args.args[0])
