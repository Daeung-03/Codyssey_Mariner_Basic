import tempfile
import unittest
from pathlib import Path

from budget_app.models import Budget, Category
from budget_app.repository import BudgetRepository, CategoryRepository


class TestCategoryRepository(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.path = Path(self._tmpdir.name) / "data" / "categories.jsonl"

    def test_creates_missing_file_empty(self):
        repo = CategoryRepository(self.path)
        self.assertEqual(list(repo.iter_categories()), [])

    def test_append_then_iter(self):
        repo = CategoryRepository(self.path)
        repo.append(Category(name="food"))
        repo.append(Category(name="transport"))
        self.assertEqual(
            [c.name for c in repo.iter_categories()], ["food", "transport"]
        )

    def test_remove_existing_returns_true_and_removes(self):
        repo = CategoryRepository(self.path)
        repo.append(Category(name="food"))
        repo.append(Category(name="transport"))
        self.assertTrue(repo.remove("food"))
        self.assertEqual([c.name for c in repo.iter_categories()], ["transport"])

    def test_remove_missing_returns_false(self):
        repo = CategoryRepository(self.path)
        repo.append(Category(name="food"))
        self.assertFalse(repo.remove("transport"))


class TestBudgetRepository(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.path = Path(self._tmpdir.name) / "data" / "budgets.jsonl"

    def test_upsert_inserts_when_month_absent(self):
        repo = BudgetRepository(self.path)
        repo.upsert(Budget(month="2024-01", amount=500000))
        self.assertEqual(repo.get("2024-01"), Budget(month="2024-01", amount=500000))

    def test_upsert_replaces_existing_month(self):
        repo = BudgetRepository(self.path)
        repo.upsert(Budget(month="2024-01", amount=500000))
        repo.upsert(Budget(month="2024-01", amount=700000))
        rows = list(repo.iter_budgets())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].amount, 700000)

    def test_get_missing_month_returns_none(self):
        repo = BudgetRepository(self.path)
        self.assertIsNone(repo.get("2099-01"))


if __name__ == "__main__":
    unittest.main()
