import tempfile
import unittest
from pathlib import Path

from budget_app.exceptions import NotFoundError, ValidationError
from budget_app.repository import CategoryRepository, TransactionRepository
from budget_app.services import CategoryService, TransactionService


class TestTransactionServiceWrite(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        base = Path(self._tmpdir.name)
        self.transaction_repo = TransactionRepository(base / "transactions.jsonl")
        self.category_service = CategoryService(CategoryRepository(base / "categories.jsonl"))
        self.service = TransactionService(self.transaction_repo, self.category_service)

    def test_next_id_starts_at_tx_000001(self):
        self.assertEqual(self.service._next_id(), "TX-000001")

    def test_next_id_increments_after_existing_rows(self):
        self.service.add(date="2024-01-01", type="income", category="etc", amount=1000)
        self.assertEqual(self.service._next_id(), "TX-000002")

    def test_add_returns_transaction_with_generated_id(self):
        t = self.service.add(date="2024-01-15", type="expense", category="food", amount=15000, memo="점심")
        self.assertEqual(t.id, "TX-000001")
        self.assertEqual(t.memo, "점심")

    def test_add_rejects_bad_date(self):
        with self.assertRaises(ValidationError):
            self.service.add(date="2024-13-40", type="expense", category="food", amount=1000)

    def test_add_rejects_non_positive_amount(self):
        with self.assertRaises(ValidationError):
            self.service.add(date="2024-01-15", type="expense", category="food", amount=0)

    def test_add_rejects_unregistered_category(self):
        with self.assertRaises(ValidationError):
            self.service.add(date="2024-01-15", type="expense", category="ghost", amount=1000)

    def test_get_existing(self):
        added = self.service.add(date="2024-01-15", type="expense", category="food", amount=1000)
        self.assertEqual(self.service.get(added.id), added)

    def test_get_missing_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.service.get("TX-999999")

    def test_update_changes_only_given_fields(self):
        added = self.service.add(date="2024-01-15", type="expense", category="food", amount=1000, memo="old")
        updated = self.service.update(added.id, amount=2000)
        self.assertEqual(updated.amount, 2000)
        self.assertEqual(updated.memo, "old")
        self.assertEqual(updated.date, "2024-01-15")

    def test_update_validates_new_values(self):
        added = self.service.add(date="2024-01-15", type="expense", category="food", amount=1000)
        with self.assertRaises(ValidationError):
            self.service.update(added.id, amount=-5)

    def test_update_missing_id_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.service.update("TX-999999", amount=2000)

    def test_delete_existing(self):
        added = self.service.add(date="2024-01-15", type="expense", category="food", amount=1000)
        self.service.delete(added.id)
        with self.assertRaises(NotFoundError):
            self.service.get(added.id)

    def test_delete_missing_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.service.delete("TX-999999")


if __name__ == "__main__":
    unittest.main()
