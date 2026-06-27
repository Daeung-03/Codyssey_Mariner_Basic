"""
저장소(Repository) 및 저장 정책 시나리오 테스트

원자적 쓰기, JSONL 포맷 정합성, 빈 줄 처리, 다중 레코드 일관성 등.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from budget_app.exceptions import StorageError
from budget_app.models import Budget, Category, Transaction
from budget_app.repository import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
    _atomic_write_lines,
)


def _make_tx(id_="TX-000001", **kw):
    defaults = dict(id=id_, type="expense", date="2024-01-01", amount=1000, category="food", memo=None, tags=[])
    defaults.update(kw)
    return Transaction(**defaults)


class TestAtomicWrite(unittest.TestCase):
    """_atomic_write_lines — temp 파일 교체 정책"""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.target = Path(self._tmpdir.name) / "test.jsonl"
        self.target.touch()

    def test_writes_lines_to_target(self):
        _atomic_write_lines(self.target, ['{"a": 1}', '{"b": 2}'])
        lines = self.target.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)

    def test_no_tmp_file_remains_after_success(self):
        _atomic_write_lines(self.target, ['{"ok": true}'])
        tmp = self.target.with_suffix(self.target.suffix + ".tmp")
        self.assertFalse(tmp.exists())

    def test_raises_storage_error_on_oserror(self):
        with patch("builtins.open", side_effect=OSError("disk full")):
            with self.assertRaises(StorageError) as ctx:
                _atomic_write_lines(self.target, ["line"])
        self.assertIn("디스크", ctx.exception.hint)


class TestTransactionRepositoryStorage(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.path = Path(self._tmpdir.name) / "data" / "tx.jsonl"

    def test_auto_creates_file_and_parent(self):
        repo = TransactionRepository(self.path)
        self.assertTrue(self.path.exists())

    def test_jsonl_each_line_is_valid_json(self):
        repo = TransactionRepository(self.path)
        repo.append(_make_tx("TX-000001"))
        repo.append(_make_tx("TX-000002", date="2024-01-02"))
        for line in self.path.read_text(encoding="utf-8").splitlines():
            obj = json.loads(line)  # 파싱 실패 시 AssertionError
            self.assertIn("id", obj)

    def test_blank_lines_in_file_are_skipped(self):
        repo = TransactionRepository(self.path)
        repo.append(_make_tx("TX-000001"))
        # 빈 줄 수동 삽입
        content = self.path.read_text(encoding="utf-8")
        self.path.write_text("\n" + content + "\n\n", encoding="utf-8")
        rows = list(repo.iter_transactions())
        self.assertEqual(len(rows), 1)

    def test_append_preserves_insertion_order(self):
        repo = TransactionRepository(self.path)
        ids = [f"TX-{i:06d}" for i in range(1, 6)]
        for i, id_ in enumerate(ids, start=1):
            repo.append(_make_tx(id_, amount=i * 100))
        result_ids = [t.id for t in repo.iter_transactions()]
        self.assertEqual(result_ids, ids)

    def test_replace_changes_only_target_row(self):
        repo = TransactionRepository(self.path)
        t1 = _make_tx("TX-000001", amount=100)
        t2 = _make_tx("TX-000002", amount=200)
        t3 = _make_tx("TX-000003", amount=300)
        for t in (t1, t2, t3):
            repo.append(t)
        updated = _make_tx("TX-000002", amount=999)
        repo.replace("TX-000002", updated)
        rows = list(repo.iter_transactions())
        self.assertEqual(rows[0].amount, 100)
        self.assertEqual(rows[1].amount, 999)
        self.assertEqual(rows[2].amount, 300)

    def test_replace_missing_id_returns_false_no_side_effect(self):
        repo = TransactionRepository(self.path)
        repo.append(_make_tx("TX-000001", amount=100))
        found = repo.replace("TX-999999", _make_tx("TX-999999"))
        self.assertFalse(found)
        self.assertEqual(list(repo.iter_transactions())[0].amount, 100)

    def test_remove_leaves_file_intact_for_remaining_rows(self):
        repo = TransactionRepository(self.path)
        repo.append(_make_tx("TX-000001"))
        repo.append(_make_tx("TX-000002", date="2024-01-02"))
        repo.remove("TX-000001")
        rows = list(repo.iter_transactions())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].id, "TX-000002")

    def test_remove_all_rows_leaves_empty_file(self):
        repo = TransactionRepository(self.path)
        repo.append(_make_tx("TX-000001"))
        repo.remove("TX-000001")
        self.assertEqual(list(repo.iter_transactions()), [])
        # 파일은 존재하되 비어 있어야 함
        self.assertTrue(self.path.exists())

    def test_write_failure_raises_storage_error(self):
        repo = TransactionRepository(self.path)
        with patch("builtins.open", side_effect=OSError("no space")):
            with self.assertRaises(StorageError):
                repo.append(_make_tx())


class TestCategoryRepositoryStorage(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.path = Path(self._tmpdir.name) / "cats.jsonl"

    def test_append_and_iter(self):
        repo = CategoryRepository(self.path)
        repo.append(Category(name="food"))
        repo.append(Category(name="transport"))
        names = [c.name for c in repo.iter_categories()]
        self.assertEqual(names, ["food", "transport"])

    def test_remove_then_iter_excludes_removed(self):
        repo = CategoryRepository(self.path)
        repo.append(Category(name="food"))
        repo.append(Category(name="transport"))
        repo.remove("food")
        names = [c.name for c in repo.iter_categories()]
        self.assertEqual(names, ["transport"])

    def test_remove_missing_name_returns_false(self):
        repo = CategoryRepository(self.path)
        self.assertFalse(repo.remove("ghost"))


class TestBudgetRepositoryStorage(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.path = Path(self._tmpdir.name) / "budgets.jsonl"

    def test_upsert_insert_new(self):
        repo = BudgetRepository(self.path)
        repo.upsert(Budget(month="2024-01", amount=500_000))
        self.assertEqual(repo.get("2024-01").amount, 500_000)

    def test_upsert_update_existing_keeps_one_row(self):
        repo = BudgetRepository(self.path)
        repo.upsert(Budget(month="2024-01", amount=300_000))
        repo.upsert(Budget(month="2024-01", amount=700_000))
        rows = list(repo.iter_budgets())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].amount, 700_000)

    def test_get_missing_returns_none(self):
        repo = BudgetRepository(self.path)
        self.assertIsNone(repo.get("2099-12"))

    def test_multiple_months_coexist(self):
        repo = BudgetRepository(self.path)
        repo.upsert(Budget(month="2024-01", amount=100_000))
        repo.upsert(Budget(month="2024-02", amount=200_000))
        self.assertEqual(repo.get("2024-01").amount, 100_000)
        self.assertEqual(repo.get("2024-02").amount, 200_000)


if __name__ == "__main__":
    unittest.main()
