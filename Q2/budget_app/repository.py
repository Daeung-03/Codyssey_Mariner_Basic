from __future__ import annotations

import json
import os
from collections.abc import Iterable, Iterator
from pathlib import Path

from budget_app.exceptions import StorageError
from budget_app.models import Budget, Category, Transaction


def _atomic_write_lines(path: Path, lines: Iterable[str]) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line if line.endswith("\n") else line + "\n")
        os.replace(tmp_path, path)
    except OSError as exc:
        raise StorageError(
            f"{path} 저장 중 오류가 발생했습니다", "디스크 공간/쓰기 권한을 확인하세요"
        ) from exc


def _ensure_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)


class TransactionRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        _ensure_file(self.path)

    def iter_transactions(self) -> Iterator[Transaction]:
        try:
            f = open(self.path, encoding="utf-8")
        except OSError as exc:
            raise StorageError(
                f"{self.path} 읽기 중 오류가 발생했습니다", "디스크 공간/쓰기 권한을 확인하세요"
            ) from exc
        with f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield Transaction.from_dict(json.loads(line))

    def _write_all(self, transactions: Iterable[Transaction]) -> None:
        lines = (json.dumps(t.to_dict(), ensure_ascii=False) for t in transactions)
        _atomic_write_lines(self.path, lines)

    def append(self, transaction: Transaction) -> None:
        rows = list(self.iter_transactions())
        rows.append(transaction)
        self._write_all(rows)

    def replace(self, transaction_id: str, updated: Transaction) -> bool:
        rows = list(self.iter_transactions())
        found = False
        for i, t in enumerate(rows):
            if t.id == transaction_id:
                rows[i] = updated
                found = True
                break
        if found:
            self._write_all(rows)
        return found

    def remove(self, transaction_id: str) -> bool:
        rows = list(self.iter_transactions())
        new_rows = [t for t in rows if t.id != transaction_id]
        found = len(new_rows) != len(rows)
        if found:
            self._write_all(new_rows)
        return found


class CategoryRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        _ensure_file(self.path)

    def iter_categories(self) -> Iterator[Category]:
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield Category.from_dict(json.loads(line))

    def _write_all(self, categories: Iterable[Category]) -> None:
        lines = (json.dumps(c.to_dict(), ensure_ascii=False) for c in categories)
        _atomic_write_lines(self.path, lines)

    def append(self, category: Category) -> None:
        rows = list(self.iter_categories())
        rows.append(category)
        self._write_all(rows)

    def remove(self, name: str) -> bool:
        rows = list(self.iter_categories())
        new_rows = [c for c in rows if c.name != name]
        found = len(new_rows) != len(rows)
        if found:
            self._write_all(new_rows)
        return found


class BudgetRepository:
    def __init__(self, path: Path) -> None:
        self.path = path
        _ensure_file(self.path)

    def iter_budgets(self) -> Iterator[Budget]:
        with open(self.path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                yield Budget.from_dict(json.loads(line))

    def _write_all(self, budgets: Iterable[Budget]) -> None:
        lines = (json.dumps(b.to_dict(), ensure_ascii=False) for b in budgets)
        _atomic_write_lines(self.path, lines)

    def upsert(self, budget: Budget) -> None:
        rows = list(self.iter_budgets())
        for i, b in enumerate(rows):
            if b.month == budget.month:
                rows[i] = budget
                self._write_all(rows)
                return
        rows.append(budget)
        self._write_all(rows)

    def get(self, month: str) -> Budget | None:
        for b in self.iter_budgets():
            if b.month == month:
                return b
        return None
