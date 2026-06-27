import csv
import unittest
from pathlib import Path

from budget_app.exceptions import EXIT_OK, EXIT_USER_ERROR
from tests.cli_test_utils import CliTestCase


class TestCmdImport(CliTestCase):
    def test_import_adds_valid_rows_and_skips_invalid(self):
        csv_path = Path(self._tmpdir.name) / "import.csv"
        csv_path.write_text(
            "date,type,category,amount,memo,tags\n"
            "2024-01-15,expense,food,15000,점심,meal\n"
            "2024-01-16,expense,ghost-category,5000,,\n"
            "2024-01-17,income,etc,100000,,\n",
            encoding="utf-8",
        )
        code, output = self.run_cli("import", "--from", str(csv_path))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("[완료] imported=2, skipped=1", output)


class TestCmdExport(CliTestCase):
    def test_export_requires_month_or_range(self):
        code, output = self.run_cli("export", "--out", str(Path(self._tmpdir.name) / "out.csv"))
        self.assertEqual(code, EXIT_USER_ERROR)

    def test_export_writes_csv_with_header_and_matching_rows(self):
        self.add_transaction("2024-01-15", "expense", "food", 15000, memo="점심", tags="meal")
        self.add_transaction("2024-02-01", "expense", "rent", 150000)
        out_path = Path(self._tmpdir.name) / "out.csv"

        code, output = self.run_cli("export", "--out", str(out_path), "--month", "2024-01")

        self.assertEqual(code, EXIT_OK)
        self.assertIn("[완료]", output)
        self.assertIn("(1 records)", output)
        with open(out_path, encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[0], ["date", "type", "category", "amount", "memo", "tags"])
        self.assertEqual(rows[1], ["2024-01-15", "expense", "food", "15000", "점심", "meal"])


if __name__ == "__main__":
    unittest.main()
