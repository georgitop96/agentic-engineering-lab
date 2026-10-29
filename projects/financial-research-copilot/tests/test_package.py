import unittest

from financial_research_copilot import __version__
from financial_research_copilot.cli import build_parser


class PackageTests(unittest.TestCase):
    def test_package_has_version(self) -> None:
        self.assertEqual(__version__, "0.1.0")

    def test_cli_parser_has_expected_program_name(self) -> None:
        self.assertEqual(build_parser().prog, "frc")
