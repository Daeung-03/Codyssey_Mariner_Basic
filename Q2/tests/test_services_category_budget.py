import tempfile
import unittest
from pathlib import Path

from budget_app.exceptions import CategoryInUseError, NotFoundError, ValidationError
from budget_app.models import Category, Transaction
from budget_app.repository import BudgetRepository, CategoryRepository, TransactionRepository
from budget_app.services import (
    BudgetService,
    CategoryService,
    validate_amount,
    validate_date,
    validate_month,
    validate_type,
)


def make_transaction(id_, category, date="2024-01-15"):
    return Transaction(id=id_, type="expense", date=date, amount=1000, category=category, memo=None, tags=[])


class TestValidators(unittest.TestCase):
    def test_validate_date_accepts_valid(self):
        validate_date("2024-01-15")  # 예외 없이 통과해야 함

    def test_validate_date_rejects_bad_format(self):
        with self.assertRaises(ValidationError):
            validate_date("2024/01/15")

    def test_validate_date_rejects_impossible_date(self):
        with self.assertRaises(ValidationError):
            validate_date("2024-13-40")

    def test_validate_month_rejects_bad_format(self):
        with self.assertRaises(ValidationError):
            validate_month("2024-1")

    def test_validate_amount_rejects_zero_and_negative(self):
        with self.assertRaises(ValidationError):
            validate_amount(0)
        with self.assertRaises(ValidationError):
            validate_amount(-100)

    def test_validate_type_rejects_unknown(self):
        with self.assertRaises(ValidationError):
            validate_type("transfer")


class TestCategoryService(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        base = Path(self._tmpdir.name)
        self.category_repo = CategoryRepository(base / "categories.jsonl")
        self.transaction_repo = TransactionRepository(base / "transactions.jsonl")

    def test_empty_repo_gets_default_categories_on_construction(self):
        service = CategoryService(self.category_repo)
        names = {c.name for c in service.list()}
        self.assertEqual(names, {"food", "transport", "rent", "etc"})

    def test_non_empty_repo_is_not_touched(self):
        self.category_repo.append(Category(name="custom"))
        service = CategoryService(self.category_repo)
        names = {c.name for c in service.list()}
        self.assertEqual(names, {"custom"})

    def test_add_rejects_duplicate(self):
        service = CategoryService(self.category_repo)
        with self.assertRaises(ValidationError):
            service.add("food")

    def test_add_new_category(self):
        service = CategoryService(self.category_repo)
        service.add("hobby")
        self.assertTrue(service.exists("hobby"))

    def test_remove_unused_category_succeeds(self):
        service = CategoryService(self.category_repo)
        service.remove("etc", self.transaction_repo)
        self.assertFalse(service.exists("etc"))

    def test_remove_missing_category_raises_not_found(self):
        service = CategoryService(self.category_repo)
        with self.assertRaises(NotFoundError):
            service.remove("does-not-exist", self.transaction_repo)

    def test_remove_in_use_category_without_reassign_raises(self):
        service = CategoryService(self.category_repo)
        self.transaction_repo.append(make_transaction("TX-000001", "food"))
        with self.assertRaises(CategoryInUseError):
            service.remove("food", self.transaction_repo)
        self.assertTrue(service.exists("food"))

    def test_remove_in_use_category_with_reassign_moves_transactions(self):
        service = CategoryService(self.category_repo)
        self.transaction_repo.append(make_transaction("TX-000001", "food"))
        service.remove("food", self.transaction_repo, reassign_to="etc")
        self.assertFalse(service.exists("food"))
        rows = list(self.transaction_repo.iter_transactions())
        self.assertEqual(rows[0].category, "etc")

    def test_remove_with_reassign_to_unknown_category_raises_not_found(self):
        service = CategoryService(self.category_repo)
        self.transaction_repo.append(make_transaction("TX-000001", "food"))
        with self.assertRaises(NotFoundError):
            service.remove("food", self.transaction_repo, reassign_to="ghost")


class TestBudgetService(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.repo = BudgetRepository(Path(self._tmpdir.name) / "budgets.jsonl")

    def test_set_budget_validates_month_and_amount(self):
        service = BudgetService(self.repo)
        with self.assertRaises(ValidationError):
            service.set_budget("2024-1", 1000)
        with self.assertRaises(ValidationError):
            service.set_budget("2024-01", 0)

    def test_set_then_get_budget(self):
        service = BudgetService(self.repo)
        service.set_budget("2024-01", 500000)
        budget = service.get_budget("2024-01")
        self.assertEqual(budget.amount, 500000)

    def test_get_missing_month_returns_none(self):
        service = BudgetService(self.repo)
        self.assertIsNone(service.get_budget("2099-01"))


if __name__ == "__main__":
    unittest.main()
