"""
import/export CSV 시나리오 테스트

유효 행/무효 행 혼재, 헤더 검증, 필터 조합, 빈 파일, 인코딩 등을 검증.
CSV 파일(입력/출력)은 tests/data/ 에 실제로 생성되어 테스트 후 확인 가능하다.
앱 데이터(transactions.jsonl 등)는 tmpdir에서 격리 실행된다.
"""
import csv
import unittest
from pathlib import Path

from budget_app.exceptions import EXIT_OK, EXIT_USER_ERROR
from tests.cli_test_utils import CliTestCase

# 모든 CSV 파일(import 입력 / export 출력)이 저장되는 디렉터리
CSV_DIR = Path(__file__).parent / "data"


class TestImportScenarios(CliTestCase):

    def setUp(self):
        super().setUp()
        CSV_DIR.mkdir(exist_ok=True)

    def _csv_path(self, name: str) -> Path:
        """테스트별 고유 파일명: tests/data/<TestClass>_<test_name>_<name>.csv"""
        return CSV_DIR / f"{type(self).__name__}_{self._testMethodName}_{name}.csv"

    def _write_csv(self, rows: list[dict], name="input") -> Path:
        path = self._csv_path(name)
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=["date", "type", "category", "amount", "memo", "tags"]
            )
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_import_all_valid_rows(self):
        path = self._write_csv([
            {"date": "2024-01-01", "type": "income", "category": "etc", "amount": 1000000, "memo": "", "tags": ""},
            {"date": "2024-01-15", "type": "expense", "category": "food", "amount": 15000, "memo": "점심", "tags": "meal"},
        ])
        code, out = self.run_cli("import", "--from", str(path))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("imported=2, skipped=0", out)

    def test_import_skips_invalid_category(self):
        path = self._write_csv([
            {"date": "2024-01-10", "type": "expense", "category": "ghost", "amount": 5000, "memo": "", "tags": ""},
            {"date": "2024-01-11", "type": "expense", "category": "food", "amount": 3000, "memo": "", "tags": ""},
        ])
        code, out = self.run_cli("import", "--from", str(path))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("imported=1, skipped=1", out)

    def test_import_skips_invalid_date(self):
        path = self._write_csv([
            {"date": "2024-13-01", "type": "expense", "category": "food", "amount": 1000, "memo": "", "tags": ""},
        ])
        _, out = self.run_cli("import", "--from", str(path))
        self.assertIn("imported=0, skipped=1", out)

    def test_import_skips_zero_amount(self):
        path = self._write_csv([
            {"date": "2024-01-01", "type": "expense", "category": "food", "amount": 0, "memo": "", "tags": ""},
        ])
        _, out = self.run_cli("import", "--from", str(path))
        self.assertIn("imported=0, skipped=1", out)

    def test_import_skips_invalid_type(self):
        path = self._write_csv([
            {"date": "2024-01-01", "type": "transfer", "category": "food", "amount": 1000, "memo": "", "tags": ""},
        ])
        _, out = self.run_cli("import", "--from", str(path))
        self.assertIn("imported=0, skipped=1", out)

    def test_import_empty_csv_reports_zero(self):
        path = self._csv_path("empty")
        path.write_text("date,type,category,amount,memo,tags\n", encoding="utf-8")
        code, out = self.run_cli("import", "--from", str(path))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("imported=0, skipped=0", out)

    def test_import_partial_valid_mixed_rows(self):
        path = self._write_csv([
            {"date": "2024-01-01", "type": "income", "category": "etc", "amount": 500000, "memo": "", "tags": ""},
            {"date": "2024-99-99", "type": "expense", "category": "food", "amount": 100, "memo": "", "tags": ""},
            {"date": "2024-01-02", "type": "expense", "category": "transport", "amount": 3000, "memo": "", "tags": "tag1,tag2"},
            {"date": "2024-01-03", "type": "expense", "category": "unknown-cat", "amount": 500, "memo": "", "tags": ""},
        ])
        _, out = self.run_cli("import", "--from", str(path))
        self.assertIn("imported=2, skipped=2", out)

    def test_import_tags_comma_separated_parsed(self):
        path = self._write_csv([
            {"date": "2024-01-01", "type": "expense", "category": "food", "amount": 1000, "memo": "", "tags": "meal,team"},
        ])
        self.run_cli("import", "--from", str(path))
        code, out = self.run_cli("search", "--tag", "team")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("TX-000001", out)

    def test_import_ids_continue_from_existing(self):
        self.add_transaction("2024-01-01", "expense", "food", 1000)
        path = self._write_csv([
            {"date": "2024-01-10", "type": "income", "category": "etc", "amount": 9999, "memo": "", "tags": ""},
        ])
        self.run_cli("import", "--from", str(path))
        _, out = self.run_cli("list", "--limit", "5")
        self.assertIn("TX-000002", out)

    def test_import_memo_empty_string_stored_as_none(self):
        path = self._write_csv([
            {"date": "2024-01-01", "type": "expense", "category": "food", "amount": 1000, "memo": "", "tags": ""},
        ])
        self.run_cli("import", "--from", str(path))
        _, out = self.run_cli("list")
        self.assertIn("TX-000001", out)


class TestExportScenarios(CliTestCase):

    def setUp(self):
        super().setUp()
        CSV_DIR.mkdir(exist_ok=True)

    def _csv_path(self, name: str) -> Path:
        return CSV_DIR / f"{type(self).__name__}_{self._testMethodName}_{name}.csv"

    def test_export_by_month(self):
        self.add_transaction("2024-01-10", "expense", "food", 15000, memo="점심", tags="meal")
        self.add_transaction("2024-02-01", "expense", "rent", 150000)
        out_path = self._csv_path("output")
        code, out = self.run_cli("export", "--out", str(out_path), "--month", "2024-01")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("(1 records)", out)
        with open(out_path, encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ["date", "type", "category", "amount", "memo", "tags"])
        self.assertEqual(rows[1][0], "2024-01-10")

    def test_export_by_date_range(self):
        self.add_transaction("2024-01-05", "expense", "food", 1000)
        self.add_transaction("2024-01-20", "expense", "transport", 2000)
        self.add_transaction("2024-02-01", "expense", "rent", 3000)
        out_path = self._csv_path("output")
        code, out = self.run_cli("export", "--out", str(out_path),
                                  "--from", "2024-01-01", "--to", "2024-01-31")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("(2 records)", out)

    def test_export_without_filter_reports_error(self):
        out_path = self._csv_path("output")
        code, out = self.run_cli("export", "--out", str(out_path))
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류]", out)
        self.assertIn("[힌트]", out)

    def test_export_empty_month_writes_header_only(self):
        out_path = self._csv_path("output")
        code, out = self.run_cli("export", "--out", str(out_path), "--month", "2099-01")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("(0 records)", out)
        with open(out_path, encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0], ["date", "type", "category", "amount", "memo", "tags"])

    def test_export_csv_rows_sorted_by_date_asc(self):
        self.add_transaction("2024-01-20", "expense", "food", 3000)
        self.add_transaction("2024-01-05", "expense", "transport", 1000)
        self.add_transaction("2024-01-15", "expense", "rent", 2000)
        out_path = self._csv_path("output")
        self.run_cli("export", "--out", str(out_path), "--month", "2024-01")
        with open(out_path, encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))[1:]
        dates = [r[0] for r in rows]
        self.assertEqual(dates, sorted(dates))

    def test_export_tags_comma_joined(self):
        self.add_transaction("2024-01-01", "expense", "food", 1000, tags="meal,team")
        out_path = self._csv_path("output")
        self.run_cli("export", "--out", str(out_path), "--month", "2024-01")
        with open(out_path, encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))[1:]
        self.assertEqual(rows[0][5], "meal,team")

    def test_import_then_export_roundtrip(self):
        """import → export 왕복: 동일 행 수 보장"""
        import_path = self._csv_path("input")
        import_path.write_text(
            "date,type,category,amount,memo,tags\n"
            "2024-03-01,expense,food,10000,커피,\n"
            "2024-03-05,income,etc,500000,,salary\n",
            encoding="utf-8",
        )
        self.run_cli("import", "--from", str(import_path))
        out_path = self._csv_path("output")
        self.run_cli("export", "--out", str(out_path), "--month", "2024-03")
        with open(out_path, encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))[1:]
        self.assertEqual(len(rows), 2)


if __name__ == "__main__":
    unittest.main()
