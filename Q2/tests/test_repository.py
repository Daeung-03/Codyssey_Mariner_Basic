import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from budget_app.exceptions import StorageError
from budget_app.models import Transaction
from budget_app.repository import TransactionRepository


def make_transaction(id_="TX-000001", date="2024-01-15", **overrides):
    fields = dict(id=id_, type="expense", date=date, amount=15000, category="food", memo=None, tags=[])
    fields.update(overrides)
    return Transaction(**fields)


class TestTransactionRepository(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.path = Path(self._tmpdir.name) / "data" / "transactions.jsonl"

    def test_creates_missing_file_and_parent_dir(self):
        repo = TransactionRepository(self.path)
        self.assertTrue(self.path.exists())
        self.assertEqual(list(repo.iter_transactions()), [])

    def test_append_then_iter_returns_in_append_order(self):
        repo = TransactionRepository(self.path)
        t1 = make_transaction("TX-000001", date="2024-01-10")
        t2 = make_transaction("TX-000002", date="2024-01-15")
        repo.append(t1)
        repo.append(t2)
        self.assertEqual(list(repo.iter_transactions()), [t1, t2])

    def test_append_leaves_no_leftover_tmp_file(self):
        repo = TransactionRepository(self.path)
        repo.append(make_transaction())
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        self.assertFalse(tmp_path.exists())

    def test_replace_existing_id_updates_fields(self):
        repo = TransactionRepository(self.path)
        repo.append(make_transaction("TX-000001", amount=15000))
        updated = make_transaction("TX-000001", amount=99999)
        found = repo.replace("TX-000001", updated)
        self.assertTrue(found)
        self.assertEqual(list(repo.iter_transactions()), [updated])

    def test_replace_missing_id_returns_false_and_leaves_file_unchanged(self):
        repo = TransactionRepository(self.path)
        original = make_transaction("TX-000001")
        repo.append(original)
        found = repo.replace("TX-999999", make_transaction("TX-999999"))
        self.assertFalse(found)
        self.assertEqual(list(repo.iter_transactions()), [original])

    def test_remove_existing_id(self):
        repo = TransactionRepository(self.path)
        t1 = make_transaction("TX-000001")
        t2 = make_transaction("TX-000002")
        repo.append(t1)
        repo.append(t2)
        found = repo.remove("TX-000001")
        self.assertTrue(found)
        self.assertEqual(list(repo.iter_transactions()), [t2])

    def test_remove_missing_id_returns_false(self):
        repo = TransactionRepository(self.path)
        repo.append(make_transaction("TX-000001"))
        self.assertFalse(repo.remove("TX-999999"))

    def test_write_failure_raises_storage_error(self):
        repo = TransactionRepository(self.path)
        with patch("builtins.open", side_effect=OSError("disk full")):
            with self.assertRaises(StorageError):
                repo.append(make_transaction())

    def test_jsonl_lines_are_one_json_object_each(self):
        repo = TransactionRepository(self.path)
        repo.append(make_transaction("TX-000001"))
        repo.append(make_transaction("TX-000002", date="2024-01-16"))
        lines = self.path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        for line in lines:
            json.loads(line)


if __name__ == "__main__":
    unittest.main()
