"""
예산(Budget) 및 summary 관련 시나리오 테스트

예산 설정/조회/갱신, summary 출력 정책(예산 미설정/설정/초과) 검증.
"""
import tempfile
import unittest
from pathlib import Path

from budget_app.exceptions import EXIT_OK, EXIT_USER_ERROR, ValidationError
from budget_app.models import Budget
from budget_app.repository import BudgetRepository, CategoryRepository, TransactionRepository
from budget_app.services import BudgetService, CategoryService, TransactionService
from tests.cli_test_utils import CliTestCase


# ---------------------------------------------------------------------------
# Service 계층 시나리오
# ---------------------------------------------------------------------------

class _ServiceBase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        base = Path(self._tmpdir.name)
        self.budget_repo = BudgetRepository(base / "budgets.jsonl")
        self.budget_svc = BudgetService(self.budget_repo)
        self.tx_repo = TransactionRepository(base / "transactions.jsonl")
        self.cat_svc = CategoryService(CategoryRepository(base / "categories.jsonl"))
        self.tx_svc = TransactionService(self.tx_repo, self.cat_svc)


class TestBudgetSetAndGet(_ServiceBase):
    """예산 설정·조회·덮어쓰기"""

    def test_set_and_get_budget(self):
        self.budget_svc.set_budget("2024-01", 500_000)
        b = self.budget_svc.get_budget("2024-01")
        self.assertEqual(b.amount, 500_000)

    def test_set_budget_overwrites_existing_month(self):
        self.budget_svc.set_budget("2024-01", 300_000)
        self.budget_svc.set_budget("2024-01", 700_000)
        b = self.budget_svc.get_budget("2024-01")
        self.assertEqual(b.amount, 700_000)

    def test_get_budget_missing_month_returns_none(self):
        self.assertIsNone(self.budget_svc.get_budget("2099-01"))

    def test_multiple_months_stored_independently(self):
        self.budget_svc.set_budget("2024-01", 500_000)
        self.budget_svc.set_budget("2024-02", 600_000)
        self.budget_svc.set_budget("2024-03", 400_000)
        self.assertEqual(self.budget_svc.get_budget("2024-01").amount, 500_000)
        self.assertEqual(self.budget_svc.get_budget("2024-02").amount, 600_000)
        self.assertEqual(self.budget_svc.get_budget("2024-03").amount, 400_000)


class TestBudgetValidation(_ServiceBase):
    """예산 입력 검증"""

    def test_rejects_zero_amount(self):
        with self.assertRaises(ValidationError) as ctx:
            self.budget_svc.set_budget("2024-01", 0)
        self.assertIn("양수", ctx.exception.message)

    def test_rejects_negative_amount(self):
        with self.assertRaises(ValidationError):
            self.budget_svc.set_budget("2024-01", -100)

    def test_rejects_bad_month_format_no_padding(self):
        with self.assertRaises(ValidationError) as ctx:
            self.budget_svc.set_budget("2024-1", 500_000)
        self.assertIn("2024-1", ctx.exception.message)

    def test_rejects_date_as_month(self):
        with self.assertRaises(ValidationError):
            self.budget_svc.set_budget("2024-01-15", 500_000)

    def test_accepts_large_budget(self):
        b = self.budget_svc.set_budget("2024-01", 999_999_999)
        self.assertEqual(b.amount, 999_999_999)

    def test_accepts_boundary_month_dec(self):
        b = self.budget_svc.set_budget("2024-12", 200_000)
        self.assertEqual(b.month, "2024-12")


class TestSummaryWithBudget(_ServiceBase):
    """summary: 예산과 결합한 사용률/초과 경고"""

    def setUp(self):
        super().setUp()
        self.tx_svc.add(date="2024-01-10", type="income", category="etc", amount=3_000_000)
        self.tx_svc.add(date="2024-01-12", type="expense", category="transport", amount=50_000)
        self.tx_svc.add(date="2024-01-20", type="expense", category="food", amount=200_000)

    def test_summary_within_budget(self):
        self.budget_svc.set_budget("2024-01", 500_000)
        r = self.tx_svc.summary("2024-01")
        self.assertEqual(r["total_expense"], 250_000)
        self.assertTrue(r["has_data"])
        # 예산 사용률 50% — over_budget 판단은 CLI 레이어가 담당
        budget = self.budget_svc.get_budget("2024-01")
        usage_pct = r["total_expense"] / budget.amount * 100
        self.assertAlmostEqual(usage_pct, 50.0)

    def test_summary_over_budget(self):
        self.budget_svc.set_budget("2024-01", 100_000)
        r = self.tx_svc.summary("2024-01")
        over = r["total_expense"] > self.budget_svc.get_budget("2024-01").amount
        self.assertTrue(over)

    def test_summary_balance_with_both_income_and_expense(self):
        r = self.tx_svc.summary("2024-01")
        self.assertEqual(r["balance"], 3_000_000 - 250_000)


# ---------------------------------------------------------------------------
# CLI 계층 시나리오
# ---------------------------------------------------------------------------

class TestCliBudgetScenarios(CliTestCase):

    def test_budget_set_and_summary_shows_usage(self):
        self.add_transaction("2024-01-10", "income", "etc", 1_000_000)
        self.add_transaction("2024-01-15", "expense", "food", 250_000)
        self.run_cli("budget", "set", "--month", "2024-01", "--amount", "500000")
        code, out = self.run_cli("summary", "--month", "2024-01")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("사용률 50.0%", out)
        self.assertNotIn("[경고]", out)

    def test_budget_set_overwrites_and_summary_reflects_new_value(self):
        self.run_cli("budget", "set", "--month", "2024-01", "--amount", "1000000")
        self.run_cli("budget", "set", "--month", "2024-01", "--amount", "300000")
        self.add_transaction("2024-01-01", "expense", "food", 200_000)
        _, out = self.run_cli("summary", "--month", "2024-01")
        # 300000 기준 사용률 66.7%
        self.assertIn("300000원", out)

    def test_summary_over_budget_shows_warning(self):
        self.add_transaction("2024-01-10", "expense", "food", 600_000)
        self.run_cli("budget", "set", "--month", "2024-01", "--amount", "500000")
        _, out = self.run_cli("summary", "--month", "2024-01")
        self.assertIn("[경고] 예산을 초과했습니다", out)

    def test_summary_without_budget_no_usage_line(self):
        self.add_transaction("2024-01-10", "expense", "food", 5000)
        code, out = self.run_cli("summary", "--month", "2024-01")
        self.assertEqual(code, EXIT_OK)
        self.assertNotIn("사용률", out)
        self.assertNotIn("예산:", out)

    def test_summary_no_data_shows_message(self):
        code, out = self.run_cli("summary", "--month", "2099-06")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("2099-06: 데이터 없음", out)

    def test_summary_top_categories_ranked_correctly(self):
        self.add_transaction("2024-01-01", "expense", "food", 10_000)
        self.add_transaction("2024-01-02", "expense", "rent", 150_000)
        self.add_transaction("2024-01-03", "expense", "transport", 5_000)
        _, out = self.run_cli("summary", "--month", "2024-01", "--top", "3")
        lines = out.splitlines()
        top_lines = [l for l in lines if l.startswith("1)") or l.startswith("2)") or l.startswith("3)")]
        self.assertTrue(top_lines[0].startswith("1) rent"))

    def test_budget_set_zero_amount_reports_error(self):
        code, out = self.run_cli("budget", "set", "--month", "2024-01", "--amount", "0")
        self.assertEqual(code, EXIT_USER_ERROR)

    def test_budget_set_bad_month_format_reports_error(self):
        code, out = self.run_cli("budget", "set", "--month", "2024-1", "--amount", "100000")
        self.assertEqual(code, EXIT_USER_ERROR)


if __name__ == "__main__":
    unittest.main()
