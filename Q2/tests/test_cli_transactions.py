import unittest
from pathlib import Path

from budget_app.exceptions import EXIT_OK, EXIT_USER_ERROR
from tests.cli_test_utils import CliTestCase


class TestCmdAdd(CliTestCase):
    def test_add_interactive_flow_prints_generated_id(self):
        code, output = self.add_transaction("2024-01-15", "expense", "food", 15000, memo="점심", tags="meal")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("[저장 완료] id=TX-000001", output)

    def test_add_with_unregistered_category_reports_error(self):
        code, output = self.add_transaction("2024-01-15", "expense", "ghost", 15000)
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류]", output)
        self.assertIn("[힌트]", output)


class TestCmdListAndSearch(CliTestCase):
    def setUp(self):
        super().setUp()
        self.add_transaction("2024-01-10", "income", "etc", 3000000)
        self.add_transaction("2024-01-15", "expense", "food", 15000, memo="점심", tags="meal")

    def test_list_shows_newest_first(self):
        code, output = self.run_cli("list", "--limit", "10")
        lines = [line for line in output.splitlines() if line.startswith("TX-")]
        self.assertEqual(code, EXIT_OK)
        self.assertTrue(lines[0].startswith("TX-000002"))

    def test_list_empty_data_dir_reports_message(self):
        empty_dir = Path(self._tmpdir.name) / "empty-data"
        code, output = self.run_cli("list", data_dir=empty_dir)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("거래 내역이 없습니다", output)

    def test_search_by_tag(self):
        code, output = self.run_cli("search", "--tag", "meal")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("TX-000002", output)
        self.assertNotIn("TX-000001", output)


class TestCmdUpdateAndDelete(CliTestCase):
    def setUp(self):
        super().setUp()
        self.add_transaction("2024-01-15", "expense", "food", 15000)

    def test_update_changes_amount(self):
        code, output = self.run_cli("update", "--id", "TX-000001", "--amount", "20000")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("[수정 완료] id=TX-000001", output)
        _, list_output = self.run_cli("list")
        self.assertIn("20000", list_output)

    def test_update_without_fields_reports_error(self):
        code, output = self.run_cli("update", "--id", "TX-000001")
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류]", output)

    def test_delete_existing(self):
        code, output = self.run_cli("delete", "--id", "TX-000001")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("[삭제 완료]", output)

    def test_delete_missing_reports_error(self):
        code, output = self.run_cli("delete", "--id", "TX-999999")
        self.assertEqual(code, EXIT_USER_ERROR)


if __name__ == "__main__":
    unittest.main()
