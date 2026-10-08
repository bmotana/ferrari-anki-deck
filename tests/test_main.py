import sys
import unittest
from unittest.mock import patch

from main import parse_args


class ParseArgsTests(unittest.TestCase):
    def test_parses_count_only_and_request_options(self):
        with patch.object(
            sys,
            "argv",
            [
                "main.py",
                "--count-only",
                "--limit",
                "5",
                "--delay",
                "0",
                "--anki-out",
                "anki.csv",
                "--kaggle-out",
                "kaggle.csv",
            ],
        ):
            args = parse_args()

        self.assertTrue(args.count_only)
        self.assertEqual(args.limit, 5)
        self.assertEqual(args.delay, 0)
        self.assertEqual(args.anki_out, "anki.csv")
        self.assertEqual(args.kaggle_out, "kaggle.csv")


if __name__ == "__main__":
    unittest.main()
