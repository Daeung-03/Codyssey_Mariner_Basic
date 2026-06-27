import unittest
from unittest.mock import patch

from budget_app.exceptions import EXIT_OK, EXIT_USER_ERROR
from tests.cli_test_utils import CliTestCase


class TestCmdSummaryAndBudget(CliTestCase):
    def test_summary_with_budget_shows_usage_and_top_categories(self):
        self.add_transaction("2024-01-10", "income", "etc", 3000000)
        self.add_transaction("2024-01-12", "expense", "transport", 20000)
        self.add_transaction("2024-01-14", "expense", "food", 45000)
        self.add_transaction("2024-01-14", "expense", "rent", 150000)
        self.run_cli("budget", "set", "--month", "2024-01", "--amount", "500000")

        code, output = self.run_cli("summary", "--month", "2024-01", "--top", "3")

        self.assertEqual(code, EXIT_OK)
        self.assertIn("총 수입: 3000000원", output)
        self.assertIn("총 지출: 215000원", output)
        self.assertIn("잔액: 2785000원", output)
        self.assertIn("사용률 43.0%", output)
        self.assertIn("1) rent 150000원", output)

    def test_summary_without_budget_skips_usage_line(self):
        self.add_transaction("2024-01-10", "income", "etc", 1000)
        code, output = self.run_cli("summary", "--month", "2024-01")
        self.assertEqual(code, EXIT_OK)
        self.assertNotIn("사용률", output)

    def test_summary_no_data_for_month_reports_message(self):
        code, output = self.run_cli("summary", "--month", "2099-12")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("2099-12: 데이터 없음", output)

    def test_summary_over_budget_warns(self):
        self.add_transaction("2024-01-10", "expense", "food", 600000)
        self.run_cli("budget", "set", "--month", "2024-01", "--amount", "500000")
        code, output = self.run_cli("summary", "--month", "2024-01")
        self.assertIn("[경고] 예산을 초과했습니다", output)

    def test_budget_set_rejects_non_positive_amount(self):
        code, output = self.run_cli("budget", "set", "--month", "2024-01", "--amount", "0")
        self.assertEqual(code, EXIT_USER_ERROR)


class TestCmdCategory(CliTestCase):
    def test_add_list_remove_unused_category(self):
        with patch("builtins.input", lambda _prompt="": "hobby"):
            code, output = self.run_cli("category", "add")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("[저장 완료] category=hobby", output)

        _, list_output = self.run_cli("category", "list")
        self.assertIn("- hobby", list_output)

        code, output = self.run_cli("category", "remove", "--name", "hobby")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("[삭제 완료] category=hobby", output)

    def test_remove_in_use_category_without_reassign_blocks(self):
        self.add_transaction("2024-01-15", "expense", "food", 1000)
        code, output = self.run_cli("category", "remove", "--name", "food")
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("--reassign-to", output)

    def test_remove_in_use_category_with_reassign_succeeds(self):
        self.add_transaction("2024-01-15", "expense", "food", 1000)
        code, output = self.run_cli("category", "remove", "--name", "food", "--reassign-to", "etc")
        self.assertEqual(code, EXIT_OK)
        _, search_output = self.run_cli("search", "--category", "etc")
        self.assertIn("TX-000001", search_output)


if __name__ == "__main__":
    unittest.main()
