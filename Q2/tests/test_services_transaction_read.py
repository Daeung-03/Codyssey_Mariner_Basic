import tempfile
import unittest
from pathlib import Path

from budget_app.repository import CategoryRepository, TransactionRepository
from budget_app.services import CategoryService, TransactionService


class TestTransactionServiceRead(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        base = Path(self._tmpdir.name)
        self.transaction_repo = TransactionRepository(base / "transactions.jsonl")
        self.category_service = CategoryService(CategoryRepository(base / "categories.jsonl"))
        self.service = TransactionService(self.transaction_repo, self.category_service)
        self.service.add(date="2024-01-10", type="income", category="etc", amount=3000000, tags=["salary"])
        self.service.add(date="2024-01-12", type="expense", category="transport", amount=20000)
        self.service.add(date="2024-01-14", type="expense", category="food", amount=45000, memo="회식", tags=["meal"])
        self.service.add(date="2024-02-01", type="expense", category="rent", amount=150000)

    def test_list_returns_newest_first(self):
        rows = self.service.list(limit=10)
        self.assertEqual([t.date for t in rows], ["2024-02-01", "2024-01-14", "2024-01-12", "2024-01-10"])

    def test_list_respects_limit(self):
        rows = self.service.list(limit=2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0].date, "2024-02-01")

    def test_search_by_category(self):
        rows = self.service.search(category="food")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].category, "food")

    def test_search_by_date_range(self):
        rows = self.service.search(date_from="2024-01-11", date_to="2024-01-31")
        self.assertEqual([t.date for t in rows], ["2024-01-14", "2024-01-12"])

    def test_search_by_query_matches_memo(self):
        rows = self.service.search(query="회식")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].memo, "회식")

    def test_search_by_tag(self):
        rows = self.service.search(tag="salary")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].category, "etc")

    def test_search_with_no_match_returns_empty_list(self):
        rows = self.service.search(category="ghost-category")
        self.assertEqual(rows, [])

    def test_summary_totals_and_balance(self):
        result = self.service.summary("2024-01", top=3)
        self.assertTrue(result["has_data"])
        self.assertEqual(result["total_income"], 3000000)
        self.assertEqual(result["total_expense"], 65000)
        self.assertEqual(result["balance"], 2935000)

    def test_summary_top_categories_sorted_descending(self):
        result = self.service.summary("2024-01", top=3)
        self.assertEqual(result["top_categories"], [("food", 45000), ("transport", 20000)])

    def test_summary_respects_top_n(self):
        result = self.service.summary("2024-01", top=1)
        self.assertEqual(result["top_categories"], [("food", 45000)])

    def test_summary_month_without_data(self):
        result = self.service.summary("2099-01", top=3)
        self.assertFalse(result["has_data"])
        self.assertEqual(result["total_income"], 0)
        self.assertEqual(result["total_expense"], 0)


if __name__ == "__main__":
    unittest.main()
