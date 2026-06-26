# 가계부 콘솔 프로그램(budget_app) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Q2.md의 파일 기반 가계부 콘솔 프로그램을 `docs/superpowers/specs/2026-06-23-budget-app-architecture-design.md`에서 합의한 4계층(CLI/Service/Repository/Model) 구조로 구현한다.

**Architecture:** CLI(argparse+대화형 입력+데코레이터) → Service(검증/비즈니스 규칙) → Repository(JSONL 스트리밍 읽기 + temp+rename 원자적 쓰기) → Model(dataclass). 모든 명령 핸들러는 `handle_errors`/`log_call`/`measure_time` 데코레이터를 이 순서로 적용한다.

**Tech Stack:** Python 3.11 (3.10+ 요구사항 충족), 표준 라이브러리만 사용. 테스트는 `pytest`가 이 환경에 설치돼 있지 않고(`python3 -m pytest` → `No module named pytest`) 과제 제약이 "표준 라이브러리만 사용"이므로 외부 패키지를 추가 설치하지 않고 표준 라이브러리 `unittest`로 작성한다.

## Global Constraints

- Python 3.10 이상, 표준 라이브러리만 사용 — 외부 패키지 설치(pip install) 금지 (Q2.md 177-181행)
- 저장 파일은 3개 이상(transactions/categories/budgets), 포맷은 JSONL 통일 (Q2.md 85-87행, 설계문서 1번)
- CLI 옵션 표기는 `--`로 통일, 모든 명령은 `--help` 지원 — argparse 기본 기능으로 충족 (Q2.md 74-75, 186행)
- 오류는 스택트레이스 대신 `[오류] 원인` + `[힌트] 해결 힌트` 출력, 종료 코드는 0이 아니어야 함 (Q2.md 155-157, 187-189행)
- 모든 쓰기 작업(add/update/delete/import/category/budget)은 temp 파일 + `os.replace`로 원자적 교체 (설계문서 4-4)
- 최소 모듈 3개 이상, 최소 클래스 2개 이상 — 본 계획은 7개 모듈(`models/exceptions/decorators/repository/services/cli/__main__`), 10개 클래스(`Transaction/Category/Budget/TransactionRepository/CategoryRepository/BudgetRepository/TransactionService/CategoryService/BudgetService/Context`)로 이를 충족
- 작업 디렉터리: 모든 경로는 `Q2/` 하위. 명령 실행/테스트는 `Q2/`를 cwd로 한다.

---

## Task 1: 프로젝트 스캐폴드 + Model 계층

**Files:**
- Create: `Q2/budget_app/__init__.py`
- Create: `Q2/budget_app/models.py`
- Create: `Q2/tests/__init__.py`
- Create: `Q2/tests/test_models.py`
- Create: `Q2/.gitignore`

**Interfaces:**
- Produces: `Transaction(id: str, type: str, date: str, amount: int, category: str, memo: str | None = None, tags: list[str] = [])` with `.to_dict() -> dict` / `Transaction.from_dict(dict) -> Transaction`
- Produces: `Category(name: str)` with `.to_dict()` / `Category.from_dict(dict)`
- Produces: `Budget(month: str, amount: int)` with `.to_dict()` / `Budget.from_dict(dict)`

- [ ] **Step 1: 디렉터리 생성 및 빈 패키지 파일 작성**

```bash
mkdir -p Q2/budget_app Q2/tests
touch Q2/budget_app/__init__.py Q2/tests/__init__.py
```

- [ ] **Step 2: 실패하는 테스트 작성 — `Q2/tests/test_models.py`**

```python
import unittest

from budget_app.models import Budget, Category, Transaction


class TestTransaction(unittest.TestCase):
    def test_round_trip(self):
        t = Transaction(
            id="TX-000001", type="expense", date="2024-01-15",
            amount=15000, category="food", memo="점심", tags=["meal"],
        )
        data = t.to_dict()
        self.assertEqual(data["id"], "TX-000001")
        restored = Transaction.from_dict(data)
        self.assertEqual(restored, t)

    def test_from_dict_defaults_memo_and_tags(self):
        data = {"id": "TX-000002", "type": "income", "date": "2024-01-01", "amount": 1000, "category": "salary"}
        restored = Transaction.from_dict(data)
        self.assertIsNone(restored.memo)
        self.assertEqual(restored.tags, [])


class TestCategory(unittest.TestCase):
    def test_round_trip(self):
        c = Category(name="food")
        self.assertEqual(Category.from_dict(c.to_dict()), c)


class TestBudget(unittest.TestCase):
    def test_round_trip(self):
        b = Budget(month="2024-01", amount=500000)
        self.assertEqual(Budget.from_dict(b.to_dict()), b)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 4: 테스트가 실패하는지 확인**

Run: `cd Q2 && python3 -m unittest tests.test_models -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'budget_app.models'`

- [ ] **Step 5: `Q2/budget_app/models.py` 구현**

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Transaction:
    id: str
    type: str  # "income" | "expense"
    date: str  # "YYYY-MM-DD"
    amount: int
    category: str
    memo: str | None = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Transaction":
        return Transaction(
            id=data["id"],
            type=data["type"],
            date=data["date"],
            amount=int(data["amount"]),
            category=data["category"],
            memo=data.get("memo"),
            tags=list(data.get("tags") or []),
        )


@dataclass
class Category:
    name: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Category":
        return Category(name=data["name"])


@dataclass
class Budget:
    month: str  # "YYYY-MM"
    amount: int

    def to_dict(self) -> dict[str, Any]:
        return {"month": self.month, "amount": self.amount}

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Budget":
        return Budget(month=data["month"], amount=int(data["amount"]))
```

- [ ] **Step 6: 테스트 통과 확인**

Run: `cd Q2 && python3 -m unittest tests.test_models -v`
Expected: `OK` (4 tests passed)

- [ ] **Step 7: 스테이징 및 커밋은 사용자가 진행**
---

## Task 2: 예외 계층 + 종료 코드

**Files:**
- Create: `Q2/budget_app/exceptions.py`
- Create: `Q2/tests/test_exceptions.py`

**Interfaces:**
- Produces: `BudgetAppError(message: str, hint: str = "")` base, attrs `.message`, `.hint`
- Produces: `ValidationError`, `NotFoundError`, `CategoryInUseError`, `StorageError` (모두 `BudgetAppError` 하위)
- Produces: `EXIT_OK = 0`, `EXIT_USER_ERROR = 1`, `EXIT_SYSTEM_ERROR = 2`
- Produces: `USER_ERROR_TYPES: tuple[type[BudgetAppError], ...]` — `(ValidationError, NotFoundError, CategoryInUseError)`

- [ ] **Step 1: 실패하는 테스트 작성 — `Q2/tests/test_exceptions.py`**

```python
import unittest

from budget_app.exceptions import (
    EXIT_OK,
    EXIT_SYSTEM_ERROR,
    EXIT_USER_ERROR,
    USER_ERROR_TYPES,
    BudgetAppError,
    CategoryInUseError,
    NotFoundError,
    StorageError,
    ValidationError,
)


class TestExceptions(unittest.TestCase):
    def test_message_and_hint_stored(self):
        exc = ValidationError("날짜 형식이 올바르지 않습니다", "예: 2024-01-15")
        self.assertEqual(exc.message, "날짜 형식이 올바르지 않습니다")
        self.assertEqual(exc.hint, "예: 2024-01-15")

    def test_hint_defaults_to_empty(self):
        exc = NotFoundError("없는 데이터입니다")
        self.assertEqual(exc.hint, "")

    def test_exit_codes(self):
        self.assertEqual(EXIT_OK, 0)
        self.assertEqual(EXIT_USER_ERROR, 1)
        self.assertEqual(EXIT_SYSTEM_ERROR, 2)

    def test_user_error_types_membership(self):
        self.assertIn(ValidationError, USER_ERROR_TYPES)
        self.assertIn(NotFoundError, USER_ERROR_TYPES)
        self.assertIn(CategoryInUseError, USER_ERROR_TYPES)
        self.assertNotIn(StorageError, USER_ERROR_TYPES)

    def test_all_inherit_from_base(self):
        for cls in (ValidationError, NotFoundError, CategoryInUseError, StorageError):
            self.assertTrue(issubclass(cls, BudgetAppError))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd Q2 && python3 -m unittest tests.test_exceptions -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'budget_app.exceptions'`

- [ ] **Step 3: `Q2/budget_app/exceptions.py` 구현**

```python
from __future__ import annotations


class BudgetAppError(Exception):
    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class ValidationError(BudgetAppError):
    pass


class NotFoundError(BudgetAppError):
    pass


class CategoryInUseError(BudgetAppError):
    pass


class StorageError(BudgetAppError):
    pass


EXIT_OK = 0
EXIT_USER_ERROR = 1
EXIT_SYSTEM_ERROR = 2

USER_ERROR_TYPES = (ValidationError, NotFoundError, CategoryInUseError)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd Q2 && python3 -m unittest tests.test_exceptions -v`
Expected: `OK` (5 tests passed)

- [ ] **Step 5: 변경분 스테이징 (커밋은 사용자가 직접 진행)**

```bash
git add Q2/budget_app/exceptions.py Q2/tests/test_exceptions.py
```

---

## Task 3: 데코레이터 (measure_time / log_call / handle_errors)

**Files:**
- Create: `Q2/budget_app/decorators.py`
- Create: `Q2/tests/test_decorators.py`

**Interfaces:**
- Consumes: `budget_app.exceptions.{BudgetAppError, ValidationError, EXIT_USER_ERROR, EXIT_SYSTEM_ERROR, USER_ERROR_TYPES}` (Task 2)
- Produces: `logger = logging.getLogger("budget_app")` (module-level, cli.py가 핸들러를 부착)
- Produces: `measure_time(func: Callable[..., int]) -> Callable[..., int]`
- Produces: `log_call(func: Callable[..., int]) -> Callable[..., int]`
- Produces: `handle_errors(func: Callable[..., int]) -> Callable[..., int]` — 모든 명령 핸들러는 `int` 종료 코드를 반환해야 하며, 이 데코레이터들은 그 계약을 보존한다. 적용 순서는 항상 `@handle_errors` → `@log_call` → `@measure_time` (위에서부터)이어야 한다.

- [ ] **Step 1: 실패하는 테스트 작성 — `Q2/tests/test_decorators.py`**

```python
import io
import logging
import unittest
from contextlib import redirect_stdout

from budget_app.decorators import handle_errors, log_call, measure_time
from budget_app.exceptions import EXIT_OK, EXIT_SYSTEM_ERROR, EXIT_USER_ERROR, NotFoundError


class TestMeasureTime(unittest.TestCase):
    def test_logs_elapsed_time_and_preserves_return_value(self):
        @measure_time
        def fn():
            return EXIT_OK

        with self.assertLogs("budget_app", level="INFO") as cm:
            result = fn()
        self.assertEqual(result, EXIT_OK)
        self.assertTrue(any("took" in msg for msg in cm.output))


class TestLogCall(unittest.TestCase):
    def test_logs_call_and_result(self):
        @log_call
        def fn(x):
            return x

        with self.assertLogs("budget_app", level="INFO") as cm:
            result = fn(EXIT_OK)
        self.assertEqual(result, EXIT_OK)
        self.assertTrue(any("CALL fn" in msg for msg in cm.output))
        self.assertTrue(any("DONE fn" in msg for msg in cm.output))


class TestHandleErrors(unittest.TestCase):
    def test_passes_through_success(self):
        @handle_errors
        def fn():
            return EXIT_OK

        self.assertEqual(fn(), EXIT_OK)

    def test_user_error_prints_cause_and_hint_and_returns_exit_1(self):
        @handle_errors
        def fn():
            raise NotFoundError("존재하지 않는 거래입니다: TX-000099", "list로 id를 확인하세요")

        buf = io.StringIO()
        with redirect_stdout(buf):
            result = fn()
        self.assertEqual(result, EXIT_USER_ERROR)
        self.assertIn("[오류] 존재하지 않는 거래입니다: TX-000099", buf.getvalue())
        self.assertIn("[힌트] list로 id를 확인하세요", buf.getvalue())

    def test_unexpected_error_does_not_leak_traceback_and_returns_exit_2(self):
        @handle_errors
        def fn():
            raise RuntimeError("예상 못한 내부 오류")

        buf = io.StringIO()
        with self.assertLogs("budget_app", level="ERROR"):
            with redirect_stdout(buf):
                result = fn()
        self.assertEqual(result, EXIT_SYSTEM_ERROR)
        self.assertNotIn("Traceback", buf.getvalue())
        self.assertIn("[오류]", buf.getvalue())

    def test_stacking_order_outer_handle_errors_catches_inner_decorator_exceptions(self):
        @handle_errors
        @log_call
        @measure_time
        def fn():
            raise NotFoundError("없는 데이터", "확인하세요")

        buf = io.StringIO()
        with self.assertLogs("budget_app", level="INFO"):
            with redirect_stdout(buf):
                result = fn()
        self.assertEqual(result, EXIT_USER_ERROR)
        self.assertIn("[오류] 없는 데이터", buf.getvalue())


if __name__ == "__main__":
    logging.getLogger("budget_app").setLevel(logging.INFO)
    unittest.main()
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd Q2 && python3 -m unittest tests.test_decorators -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'budget_app.decorators'`

- [ ] **Step 3: `Q2/budget_app/decorators.py` 구현**

```python
from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import Any

from budget_app.exceptions import (
    EXIT_SYSTEM_ERROR,
    EXIT_USER_ERROR,
    BudgetAppError,
    USER_ERROR_TYPES,
)

logger = logging.getLogger("budget_app")


def measure_time(func: Callable[..., int]) -> Callable[..., int]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> int:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            logger.info("%s took %.4fs", func.__name__, elapsed)

    return wrapper


def log_call(func: Callable[..., int]) -> Callable[..., int]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> int:
        logger.info("CALL %s args=%r kwargs=%r", func.__name__, args, kwargs)
        result = func(*args, **kwargs)
        logger.info("DONE %s -> exit=%s", func.__name__, result)
        return result

    return wrapper


def handle_errors(func: Callable[..., int]) -> Callable[..., int]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> int:
        try:
            return func(*args, **kwargs)
        except USER_ERROR_TYPES as exc:
            print(f"[오류] {exc.message}")
            if exc.hint:
                print(f"[힌트] {exc.hint}")
            return EXIT_USER_ERROR
        except BudgetAppError as exc:
            print(f"[오류] {exc.message}")
            if exc.hint:
                print(f"[힌트] {exc.hint}")
            return EXIT_SYSTEM_ERROR
        except Exception:
            logger.exception("Unexpected error in %s", func.__name__)
            print("[오류] 예기치 못한 문제가 발생했습니다.")
            print("[힌트] logs/app.log에서 자세한 내용을 확인하세요.")
            return EXIT_SYSTEM_ERROR

    return wrapper
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd Q2 && python3 -m unittest tests.test_decorators -v`
Expected: `OK` (6 tests passed)

- [ ] **Step 5: 스테이징 및 커밋은 사용자가 진행**
---

## Task 4: Repository 계층 — 원자적 쓰기 헬퍼 + TransactionRepository

**Files:**
- Create: `Q2/budget_app/repository.py`
- Create: `Q2/tests/test_repository.py`

**Interfaces:**
- Consumes: `budget_app.models.Transaction` (Task 1), `budget_app.exceptions.StorageError` (Task 2)
- Produces: `_atomic_write_lines(path: Path, lines: Iterable[str]) -> None` (module-private, temp 파일 + `os.replace`)
- Produces: `TransactionRepository(path: Path)` with `.iter_transactions() -> Iterator[Transaction]`, `.append(transaction: Transaction) -> None`, `.replace(transaction_id: str, updated: Transaction) -> bool`, `.remove(transaction_id: str) -> bool`. 생성자가 파일/부모 폴더를 없으면 만든다.

- [ ] **Step 1: 실패하는 테스트 작성 — `Q2/tests/test_repository.py`**

```python
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
            json.loads(line)  # 한 줄 = 완전한 JSON 객체


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd Q2 && python3 -m unittest tests.test_repository -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'budget_app.repository'`

- [ ] **Step 3: `Q2/budget_app/repository.py` 구현 (Part 1 — 공용 헬퍼 + TransactionRepository)**

```python
from __future__ import annotations

import json
import os
from collections.abc import Iterable, Iterator
from pathlib import Path

from budget_app.exceptions import StorageError
from budget_app.models import Transaction


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
        with open(self.path, encoding="utf-8") as f:
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
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd Q2 && python3 -m unittest tests.test_repository -v`
Expected: `OK` (9 tests passed)

- [ ] **Step 5: 변경분 스테이징 (커밋은 사용자가 직접 진행)**

```bash
git add Q2/budget_app/repository.py Q2/tests/test_repository.py
```

---

## Task 5: Repository 계층 — CategoryRepository + BudgetRepository

**Files:**
- Modify: `Q2/budget_app/repository.py` (Task 4에서 만든 파일에 추가)
- Create: `Q2/tests/test_repository_category_budget.py`

**Interfaces:**
- Consumes: `_atomic_write_lines`, `_ensure_file` (Task 4, 같은 파일 내 private 헬퍼), `budget_app.models.{Category, Budget}` (Task 1)
- Produces: `CategoryRepository(path: Path)` with `.iter_categories() -> Iterator[Category]`, `.append(category: Category) -> None`, `.remove(name: str) -> bool`
- Produces: `BudgetRepository(path: Path)` with `.iter_budgets() -> Iterator[Budget]`, `.upsert(budget: Budget) -> None` (같은 month면 교체, 없으면 추가), `.get(month: str) -> Budget | None`

- [ ] **Step 1: 실패하는 테스트 작성 — `Q2/tests/test_repository_category_budget.py`**

```python
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
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd Q2 && python3 -m unittest tests.test_repository_category_budget -v`
Expected: FAIL with `ImportError: cannot import name 'CategoryRepository' from 'budget_app.repository'`

- [ ] **Step 3: `Q2/budget_app/repository.py` 끝에 추가**

```python
from budget_app.models import Budget, Category  # 파일 상단 import에 합친다


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
```

**참고**: `Q2/budget_app/repository.py` 파일 맨 위 import 줄을 `from budget_app.models import Budget, Category, Transaction`로 한 줄로 합쳐서 정리한다 (Task 4에서는 `Transaction`만 import했었다).

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd Q2 && python3 -m unittest tests.test_repository_category_budget -v`
Expected: `OK` (7 tests passed)

- [ ] **Step 5: 스테이징 및 커밋 사용자가 진행**

---

## Task 6: Service 계층 — 검증 함수 + CategoryService + BudgetService

**Files:**
- Create: `Q2/budget_app/services.py`
- Create: `Q2/tests/test_services_category_budget.py`

**Interfaces:**
- Consumes: `CategoryRepository`, `BudgetRepository`, `TransactionRepository` (Task 4/5), `Category`, `Budget`, `Transaction` (Task 1), `ValidationError`, `NotFoundError`, `CategoryInUseError` (Task 2)
- Produces: `validate_date(value: str) -> None`, `validate_month(value: str) -> None`, `validate_amount(value: int) -> None`, `validate_type(value: str) -> None` (모두 실패 시 `ValidationError` 발생)
- Produces: `DEFAULT_CATEGORIES: tuple[str, ...]` = `("food", "transport", "rent", "etc")`
- Produces: `CategoryService(repo: CategoryRepository)` — 생성 시 `repo`가 비어 있으면 `DEFAULT_CATEGORIES`를 자동 등록. `.list() -> list[Category]`, `.exists(name: str) -> bool`, `.add(name: str) -> Category`, `.remove(name: str, transaction_repo: TransactionRepository, reassign_to: str | None = None) -> None`
- Produces: `BudgetService(repo: BudgetRepository)` — `.set_budget(month: str, amount: int) -> Budget`, `.get_budget(month: str) -> Budget | None`

- [ ] **Step 1: 실패하는 테스트 작성 — `Q2/tests/test_services_category_budget.py`**

```python
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
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd Q2 && python3 -m unittest tests.test_services_category_budget -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'budget_app.services'`

- [ ] **Step 3: `Q2/budget_app/services.py` 구현 (Part 1)**

```python
from __future__ import annotations

import re
from dataclasses import replace as dc_replace
from datetime import date as date_cls

from budget_app.exceptions import CategoryInUseError, NotFoundError, ValidationError
from budget_app.models import Budget, Category
from budget_app.repository import BudgetRepository, CategoryRepository, TransactionRepository

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
DEFAULT_CATEGORIES = ("food", "transport", "rent", "etc")
VALID_TYPES = ("income", "expense")


def validate_date(value: str) -> None:
    if not DATE_RE.match(value):
        raise ValidationError(f"날짜 형식이 올바르지 않습니다: {value}", "예: 2024-01-15")
    year, month, day = (int(part) for part in value.split("-"))
    try:
        date_cls(year, month, day)
    except ValueError as exc:
        raise ValidationError(f"날짜 형식이 올바르지 않습니다: {value}", "예: 2024-01-15") from exc


def validate_month(value: str) -> None:
    if not MONTH_RE.match(value):
        raise ValidationError(f"월 형식이 올바르지 않습니다: {value}", "예: 2024-01")


def validate_amount(value: int) -> None:
    if value <= 0:
        raise ValidationError(f"금액은 양수여야 합니다: {value}", "예: 15000")


def validate_type(value: str) -> None:
    if value not in VALID_TYPES:
        raise ValidationError(
            f"허용되지 않은 타입입니다: {value}", "income 또는 expense 중 하나를 입력하세요"
        )


class CategoryService:
    def __init__(self, repo: CategoryRepository) -> None:
        self.repo = repo
        if not any(True for _ in self.repo.iter_categories()):
            for name in DEFAULT_CATEGORIES:
                self.repo.append(Category(name=name))

    def list(self) -> list[Category]:
        return list(self.repo.iter_categories())

    def exists(self, name: str) -> bool:
        return any(c.name == name for c in self.repo.iter_categories())

    def add(self, name: str) -> Category:
        if self.exists(name):
            raise ValidationError(f"이미 존재하는 카테고리입니다: {name}", "다른 이름을 사용하세요")
        category = Category(name=name)
        self.repo.append(category)
        return category

    def remove(
        self,
        name: str,
        transaction_repo: TransactionRepository,
        reassign_to: str | None = None,
    ) -> None:
        if not self.exists(name):
            raise NotFoundError(f"존재하지 않는 카테고리입니다: {name}", "category list로 확인하세요")
        in_use = [t for t in transaction_repo.iter_transactions() if t.category == name]
        if in_use:
            if not reassign_to:
                raise CategoryInUseError(
                    f"'{name}' 카테고리를 사용 중인 거래가 {len(in_use)}건 있습니다",
                    "--reassign-to <다른카테고리>를 지정해 대체 후 삭제하세요",
                )
            if not self.exists(reassign_to):
                raise NotFoundError(
                    f"존재하지 않는 카테고리입니다: {reassign_to}", "category list로 확인하세요"
                )
            for t in in_use:
                transaction_repo.replace(t.id, dc_replace(t, category=reassign_to))
        self.repo.remove(name)


class BudgetService:
    def __init__(self, repo: BudgetRepository) -> None:
        self.repo = repo

    def set_budget(self, month: str, amount: int) -> Budget:
        validate_month(month)
        validate_amount(amount)
        budget = Budget(month=month, amount=amount)
        self.repo.upsert(budget)
        return budget

    def get_budget(self, month: str) -> Budget | None:
        return self.repo.get(month)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd Q2 && python3 -m unittest tests.test_services_category_budget -v`
Expected: `OK` (18 tests passed)

- [ ] **Step 5: 스테이징 및 커밋은 사용자가 진행**

---

## Task 7: Service 계층 — TransactionService 쓰기 경로 (add/get/update/delete)

**Files:**
- Modify: `Q2/budget_app/services.py` (Task 6 파일에 추가)
- Create: `Q2/tests/test_services_transaction_write.py`

**Interfaces:**
- Consumes: `TransactionRepository` (Task 4), `CategoryService` (Task 6), `Transaction` (Task 1), `ValidationError`/`NotFoundError` (Task 2)
- Produces: `TransactionService(repo: TransactionRepository, category_service: CategoryService)` with
  - `._next_id() -> str` (private이지만 테스트에서 직접 호출해 `"TX-000001"` 포맷을 확인)
  - `.add(date: str, type: str, category: str, amount: int, memo: str | None = None, tags: list[str] | None = None) -> Transaction`
  - `.get(transaction_id: str) -> Transaction` (없으면 `NotFoundError`)
  - `.update(transaction_id: str, date=None, type=None, category=None, amount=None, memo=None, tags=None) -> Transaction` (지정한 필드만 변경, `None`은 "변경 안 함")
  - `.delete(transaction_id: str) -> None` (없으면 `NotFoundError`)

- [ ] **Step 1: 실패하는 테스트 작성 — `Q2/tests/test_services_transaction_write.py`**

```python
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
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd Q2 && python3 -m unittest tests.test_services_transaction_write -v`
Expected: FAIL with `ImportError: cannot import name 'TransactionService' from 'budget_app.services'`

- [ ] **Step 3: `Q2/budget_app/services.py` 끝에 추가**

```python
from budget_app.models import Transaction  # 파일 상단 import에 합친다 (Budget, Category, Transaction)
from budget_app.repository import TransactionRepository  # 상단 import에 합친다


class TransactionService:
    def __init__(self, repo: TransactionRepository, category_service: CategoryService) -> None:
        self.repo = repo
        self.category_service = category_service

    def _next_id(self) -> str:
        max_seq = 0
        for t in self.repo.iter_transactions():
            try:
                seq = int(t.id.split("-")[1])
            except (IndexError, ValueError):
                continue
            max_seq = max(max_seq, seq)
        return f"TX-{max_seq + 1:06d}"

    def _validate_fields(self, date: str, type: str, category: str, amount: int) -> None:
        validate_date(date)
        validate_type(type)
        validate_amount(amount)
        if not self.category_service.exists(category):
            raise ValidationError(
                f"존재하지 않는 카테고리입니다: {category}", "category add로 먼저 등록하세요"
            )

    def add(
        self,
        date: str,
        type: str,
        category: str,
        amount: int,
        memo: str | None = None,
        tags: list[str] | None = None,
    ) -> Transaction:
        self._validate_fields(date, type, category, amount)
        transaction = Transaction(
            id=self._next_id(), type=type, date=date, amount=amount,
            category=category, memo=memo, tags=tags or [],
        )
        self.repo.append(transaction)
        return transaction

    def get(self, transaction_id: str) -> Transaction:
        for t in self.repo.iter_transactions():
            if t.id == transaction_id:
                return t
        raise NotFoundError(f"존재하지 않는 거래입니다: {transaction_id}", "list로 id를 확인하세요")

    def update(
        self,
        transaction_id: str,
        date: str | None = None,
        type: str | None = None,
        category: str | None = None,
        amount: int | None = None,
        memo: str | None = None,
        tags: list[str] | None = None,
    ) -> Transaction:
        current = self.get(transaction_id)
        merged = dc_replace(
            current,
            date=date if date is not None else current.date,
            type=type if type is not None else current.type,
            category=category if category is not None else current.category,
            amount=amount if amount is not None else current.amount,
            memo=memo if memo is not None else current.memo,
            tags=tags if tags is not None else current.tags,
        )
        self._validate_fields(merged.date, merged.type, merged.category, merged.amount)
        self.repo.replace(transaction_id, merged)
        return merged

    def delete(self, transaction_id: str) -> None:
        self.get(transaction_id)  # 없으면 NotFoundError 발생
        self.repo.remove(transaction_id)
```

**참고**: `Q2/budget_app/services.py` 상단 import를 다음처럼 정리한다 — `from budget_app.models import Budget, Category, Transaction`, `from budget_app.repository import BudgetRepository, CategoryRepository, TransactionRepository`.

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd Q2 && python3 -m unittest tests.test_services_transaction_write -v`
Expected: `OK` (13 tests passed)

- [ ] **Step 5: 사용자가 스테이징 및 커밋**

---

## Task 8: Service 계층 — TransactionService 읽기 경로 (list/search/summary)

**Files:**
- Modify: `Q2/budget_app/services.py` (Task 7 파일에 추가)
- Create: `Q2/tests/test_services_transaction_read.py`

**Interfaces:**
- Consumes: `TransactionService.add` (Task 7, 테스트 fixture 데이터 생성용)
- Produces: `TransactionService.list(limit: int = 20) -> list[Transaction]` (날짜 역순, 동일 날짜는 id 역순)
- Produces: `TransactionService.search(date_from=None, date_to=None, category=None, type=None, query=None, tag=None) -> list[Transaction]` (AND 결합 필터, 날짜 역순)
- Produces: `TransactionService.summary(month: str, top: int = 3) -> dict` — 키: `has_data: bool`, `total_income: int`, `total_expense: int`, `balance: int`, `top_categories: list[tuple[str, int]]`

- [ ] **Step 1: 실패하는 테스트 작성 — `Q2/tests/test_services_transaction_read.py`**

```python
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
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd Q2 && python3 -m unittest tests.test_services_transaction_read -v`
Expected: FAIL with `AttributeError: 'TransactionService' object has no attribute 'list'`

- [ ] **Step 3: `Q2/budget_app/services.py`의 `TransactionService` 안, `delete` 메서드 뒤에 추가**

```python
    def list(self, limit: int = 20) -> list[Transaction]:
        rows = list(self.repo.iter_transactions())
        rows.sort(key=lambda t: (t.date, t.id), reverse=True)
        return rows[:limit]

    def search(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
        category: str | None = None,
        type: str | None = None,
        query: str | None = None,
        tag: str | None = None,
    ) -> list[Transaction]:
        def matches(t: Transaction) -> bool:
            if date_from and t.date < date_from:
                return False
            if date_to and t.date > date_to:
                return False
            if category and t.category != category:
                return False
            if type and t.type != type:
                return False
            if query and query not in (t.memo or ""):
                return False
            if tag and tag not in t.tags:
                return False
            return True

        rows = [t for t in self.repo.iter_transactions() if matches(t)]
        rows.sort(key=lambda t: (t.date, t.id), reverse=True)
        return rows

    def summary(self, month: str, top: int = 3) -> dict:
        rows = [t for t in self.repo.iter_transactions() if t.date.startswith(month)]
        total_income = sum(t.amount for t in rows if t.type == "income")
        total_expense = sum(t.amount for t in rows if t.type == "expense")
        by_category: dict[str, int] = {}
        for t in rows:
            if t.type == "expense":
                by_category[t.category] = by_category.get(t.category, 0) + t.amount
        top_categories = sorted(by_category.items(), key=lambda kv: kv[1], reverse=True)[:top]
        return {
            "has_data": bool(rows),
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "top_categories": top_categories,
        }
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd Q2 && python3 -m unittest tests.test_services_transaction_read -v`
Expected: `OK` (11 tests passed)

- [ ] **Step 5: 사용자가 스테이징 및 커밋**

---

## Task 9: CLI 계층 — 파서/Context + add/list/search/update/delete

**Files:**
- Create: `Q2/budget_app/cli.py`
- Create: `Q2/tests/cli_test_utils.py`
- Create: `Q2/tests/test_cli_transactions.py`

**Interfaces:**
- Consumes: `handle_errors/log_call/measure_time` (Task 3), `TransactionRepository/CategoryRepository/BudgetRepository` (Task 4/5), `TransactionService/CategoryService/BudgetService` (Task 6/7/8), `EXIT_OK/EXIT_USER_ERROR/ValidationError` (Task 2)
- Produces: `Context(data_dir: Path)` — `.transaction_repo`, `.category_repo`, `.budget_repo`, `.category_service`, `.transaction_service`, `.budget_service` 속성
- Produces: `build_parser() -> argparse.ArgumentParser` (이번 Task에서는 `add/list/search/update/delete` 서브커맨드만)
- Produces: `dispatch(args: argparse.Namespace, ctx: Context) -> int`
- Produces: `main(argv: list[str] | None = None, log_dir: Path | None = None) -> int` — `log_dir`은 테스트에서 실제 `logs/app.log`를 건드리지 않도록 주입 지점. 이후 Task 10/11에서 `build_parser`/`COMMAND_HANDLERS`를 계속 확장한다.
- Produces: `Q2/tests/cli_test_utils.py`의 `CliTestCase(unittest.TestCase)` — `.run_cli(*args, data_dir=None) -> tuple[int, str]`, `.add_transaction(date, type_, category, amount, memo="", tags="") -> tuple[int, str]`.이후 Task 10/11의 CLI 테스트가 이 클래스를 그대로 재사용한다(중복 정의 금지).

- [ ] **Step 1: 실패하는 테스트 작성 — `Q2/tests/cli_test_utils.py`, `Q2/tests/test_cli_transactions.py`**

`Q2/tests/cli_test_utils.py` (테스트 헬퍼 — Task 10/11에서도 그대로 import해서 재사용한다. `budget_app.cli`가 아직 없으므로 이 파일을 import하는 순간 실패한다):

```python
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from budget_app import cli


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.data_dir = Path(self._tmpdir.name) / "data"
        self.log_dir = Path(self._tmpdir.name) / "logs"

    def run_cli(self, *args, data_dir=None):
        argv = ["--data-dir", str(data_dir or self.data_dir), *args]
        buf = StringIO()
        with redirect_stdout(buf):
            code = cli.main(argv, log_dir=self.log_dir)
        return code, buf.getvalue()

    def add_transaction(self, date, type_, category, amount, memo="", tags=""):
        answers = iter([date, type_, category, str(amount), memo, tags])
        with patch("builtins.input", lambda _prompt="": next(answers)):
            return self.run_cli("add")
```

`Q2/tests/test_cli_transactions.py`:

```python
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
```

**참고**: 위 두 테스트는 같은 `patch` import를 쓰지 않는다 — `add_transaction`은 `cli_test_utils.py` 안에서만 `unittest.mock.patch`를 사용하고, `test_cli_transactions.py`는 더 이상 직접 `input()`을 패치하지 않는다.

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd Q2 && python3 -m unittest tests.test_cli_transactions -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'budget_app.cli'`

- [ ] **Step 3: `Q2/budget_app/cli.py` 구현 (Part 1)**

```python
from __future__ import annotations

import argparse
import logging
from collections.abc import Callable
from pathlib import Path

from budget_app.decorators import handle_errors, log_call, measure_time
from budget_app.exceptions import EXIT_OK, ValidationError
from budget_app.repository import BudgetRepository, CategoryRepository, TransactionRepository
from budget_app.services import BudgetService, CategoryService, TransactionService


class Context:
    def __init__(self, data_dir: Path) -> None:
        self.transaction_repo = TransactionRepository(data_dir / "transactions.jsonl")
        self.category_repo = CategoryRepository(data_dir / "categories.jsonl")
        self.budget_repo = BudgetRepository(data_dir / "budgets.jsonl")
        self.category_service = CategoryService(self.category_repo)
        self.transaction_service = TransactionService(self.transaction_repo, self.category_service)
        self.budget_service = BudgetService(self.budget_repo)


def _parse_amount(raw: str) -> int:
    try:
        return int(raw.strip())
    except ValueError as exc:
        raise ValidationError(f"금액은 숫자여야 합니다: {raw}", "예: 15000") from exc


def _read_tags(raw: str) -> list[str]:
    return [t.strip() for t in raw.split(",") if t.strip()]


def _print_transactions(rows) -> None:
    for t in rows:
        print(f"{t.id} | {t.date} | {t.type} | {t.category} | {t.amount} | {t.memo or ''}")


@handle_errors
@log_call
@measure_time
def cmd_add(args: argparse.Namespace, ctx: Context) -> int:
    date = input("날짜(YYYY-MM-DD): ").strip()
    type_ = input("타입(income/expense): ").strip()
    category = input("카테고리: ").strip()
    amount = _parse_amount(input("금액(양수): "))
    memo = input("메모(선택): ").strip() or None
    tags = _read_tags(input("태그(쉼표로 구분, 없으면 엔터): "))
    transaction = ctx.transaction_service.add(date, type_, category, amount, memo, tags)
    print(f"[저장 완료] id={transaction.id}")
    return EXIT_OK


@handle_errors
@log_call
@measure_time
def cmd_list(args: argparse.Namespace, ctx: Context) -> int:
    rows = ctx.transaction_service.list(limit=args.limit)
    if not rows:
        print("거래 내역이 없습니다")
        return EXIT_OK
    _print_transactions(rows)
    return EXIT_OK


@handle_errors
@log_call
@measure_time
def cmd_search(args: argparse.Namespace, ctx: Context) -> int:
    rows = ctx.transaction_service.search(
        date_from=args.date_from, date_to=args.date_to, category=args.category,
        type=args.type, query=args.q, tag=args.tag,
    )
    if not rows:
        print("조건에 맞는 거래가 없습니다")
        return EXIT_OK
    _print_transactions(rows)
    return EXIT_OK


@handle_errors
@log_call
@measure_time
def cmd_update(args: argparse.Namespace, ctx: Context) -> int:
    if all(v is None for v in (args.date, args.type, args.category, args.amount, args.memo, args.tags)):
        raise ValidationError("변경할 필드가 지정되지 않았습니다", "예: update --id TX-000001 --amount 20000")
    tags = _read_tags(args.tags) if args.tags is not None else None
    updated = ctx.transaction_service.update(
        args.id, date=args.date, type=args.type, category=args.category,
        amount=args.amount, memo=args.memo, tags=tags,
    )
    print(f"[수정 완료] id={updated.id}")
    return EXIT_OK


@handle_errors
@log_call
@measure_time
def cmd_delete(args: argparse.Namespace, ctx: Context) -> int:
    ctx.transaction_service.delete(args.id)
    print(f"[삭제 완료] id={args.id}")
    return EXIT_OK


COMMAND_HANDLERS: dict[str, Callable[[argparse.Namespace, Context], int]] = {
    "add": cmd_add,
    "list": cmd_list,
    "search": cmd_search,
    "update": cmd_update,
    "delete": cmd_delete,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="budget_app")
    parser.add_argument("--data-dir", default="./data")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("add")

    p_list = sub.add_parser("list")
    p_list.add_argument("--limit", type=int, default=20)

    p_search = sub.add_parser("search")
    p_search.add_argument("--from", dest="date_from")
    p_search.add_argument("--to", dest="date_to")
    p_search.add_argument("--category")
    p_search.add_argument("--type")
    p_search.add_argument("--q")
    p_search.add_argument("--tag")

    p_update = sub.add_parser("update")
    p_update.add_argument("--id", required=True)
    p_update.add_argument("--date")
    p_update.add_argument("--type")
    p_update.add_argument("--category")
    p_update.add_argument("--amount", type=int)
    p_update.add_argument("--memo")
    p_update.add_argument("--tags")

    p_delete = sub.add_parser("delete")
    p_delete.add_argument("--id", required=True)

    return parser


def dispatch(args: argparse.Namespace, ctx: Context) -> int:
    handler = COMMAND_HANDLERS[args.command]
    return handler(args, ctx)


def main(argv: list[str] | None = None, log_dir: Path | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    log_dir = log_dir or Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_dir / "app.log", level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s", force=True,
    )
    ctx = Context(Path(args.data_dir))
    return dispatch(args, ctx)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd Q2 && python3 -m unittest tests.test_cli_transactions -v`
Expected: `OK` (9 tests passed)

- [ ] **Step 5: 사용자가 스테이징 및 커밋**

---

## Task 10: CLI 계층 — summary/budget/category

**Files:**
- Modify: `Q2/budget_app/cli.py` (Task 9 파일에 추가/수정)
- Create: `Q2/tests/test_cli_summary_budget_category.py`

**Interfaces:**
- Consumes: `Context` (Task 9), `tests.cli_test_utils.CliTestCase`(Task 9 — 그대로 import해서 재사용, 다시 정의하지 않음), `TransactionService.summary`/`BudgetService.{set_budget,get_budget}`/`CategoryService.{add,list,remove}` (Task 6/8)
- Produces: `cmd_summary`, `cmd_budget_set`, `cmd_category_add`, `cmd_category_list`, `cmd_category_remove` — 모두 기존과 동일하게 `(args, ctx) -> int` 시그니처
- `build_parser()`에 `summary --month --top`, `budget set --month --amount`, `category add|list|remove --name --reassign-to` 서브커맨드 추가
- `dispatch()`가 `budget`/`category`의 2단계 서브커맨드(`args.budget_command`, `args.category_command`)를 처리하도록 확장

- [ ] **Step 1: 실패하는 테스트 작성 — `Q2/tests/test_cli_summary_budget_category.py`**

```python
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
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd Q2 && python3 -m unittest tests.test_cli_summary_budget_category -v`
Expected: FAIL with `error: argument command: invalid choice: 'summary'`

- [ ] **Step 3: `Q2/budget_app/cli.py` 수정 — 핸들러 추가**

`cmd_delete` 함수 뒤, `COMMAND_HANDLERS` 선언 앞에 추가:

```python
@handle_errors
@log_call
@measure_time
def cmd_summary(args: argparse.Namespace, ctx: Context) -> int:
    result = ctx.transaction_service.summary(args.month, args.top)
    if not result["has_data"]:
        print(f"{args.month}: 데이터 없음")
    print(f"총 수입: {result['total_income']}원")
    print(f"총 지출: {result['total_expense']}원")
    print(f"잔액: {result['balance']}원")
    budget = ctx.budget_service.get_budget(args.month)
    if budget:
        usage = (result["total_expense"] / budget.amount * 100) if budget.amount else 0.0
        print(f"예산: {budget.amount}원 (사용률 {usage:.1f}%)")
        if result["total_expense"] > budget.amount:
            print("[경고] 예산을 초과했습니다")
    if result["top_categories"]:
        print(f"\n지출 TOP {args.top}")
        for i, (category, amount) in enumerate(result["top_categories"], start=1):
            print(f"{i}) {category} {amount}원")
    return EXIT_OK


@handle_errors
@log_call
@measure_time
def cmd_budget_set(args: argparse.Namespace, ctx: Context) -> int:
    budget = ctx.budget_service.set_budget(args.month, args.amount)
    print(f"[저장 완료] {budget.month} 예산 {budget.amount}원")
    return EXIT_OK


@handle_errors
@log_call
@measure_time
def cmd_category_add(args: argparse.Namespace, ctx: Context) -> int:
    name = input("카테고리명: ").strip()
    category = ctx.category_service.add(name)
    print(f"[저장 완료] category={category.name}")
    return EXIT_OK


@handle_errors
@log_call
@measure_time
def cmd_category_list(args: argparse.Namespace, ctx: Context) -> int:
    for c in ctx.category_service.list():
        print(f"- {c.name}")
    return EXIT_OK


@handle_errors
@log_call
@measure_time
def cmd_category_remove(args: argparse.Namespace, ctx: Context) -> int:
    ctx.category_service.remove(args.name, ctx.transaction_repo, reassign_to=args.reassign_to)
    print(f"[삭제 완료] category={args.name}")
    return EXIT_OK
```

`COMMAND_HANDLERS` 선언을 다음으로 교체:

```python
COMMAND_HANDLERS: dict[str, Callable[[argparse.Namespace, Context], int]] = {
    "add": cmd_add,
    "list": cmd_list,
    "search": cmd_search,
    "update": cmd_update,
    "delete": cmd_delete,
    "summary": cmd_summary,
}

BUDGET_HANDLERS: dict[str, Callable[[argparse.Namespace, Context], int]] = {
    "set": cmd_budget_set,
}

CATEGORY_HANDLERS: dict[str, Callable[[argparse.Namespace, Context], int]] = {
    "add": cmd_category_add,
    "list": cmd_category_list,
    "remove": cmd_category_remove,
}
```

`build_parser()`의 `return parser` 바로 앞에 추가:

```python
    p_summary = sub.add_parser("summary")
    p_summary.add_argument("--month", required=True)
    p_summary.add_argument("--top", type=int, default=3)

    p_budget = sub.add_parser("budget")
    budget_sub = p_budget.add_subparsers(dest="budget_command", required=True)
    p_budget_set = budget_sub.add_parser("set")
    p_budget_set.add_argument("--month", required=True)
    p_budget_set.add_argument("--amount", type=int, required=True)

    p_category = sub.add_parser("category")
    category_sub = p_category.add_subparsers(dest="category_command", required=True)
    category_sub.add_parser("add")
    category_sub.add_parser("list")
    p_category_remove = category_sub.add_parser("remove")
    p_category_remove.add_argument("--name", required=True)
    p_category_remove.add_argument("--reassign-to")
```

`dispatch()`를 다음으로 교체:

```python
def dispatch(args: argparse.Namespace, ctx: Context) -> int:
    if args.command == "budget":
        return BUDGET_HANDLERS[args.budget_command](args, ctx)
    if args.command == "category":
        return CATEGORY_HANDLERS[args.category_command](args, ctx)
    return COMMAND_HANDLERS[args.command](args, ctx)
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd Q2 && python3 -m unittest tests.test_cli_summary_budget_category -v`
Expected: `OK` (8 tests passed)

Run (회귀 확인): `cd Q2 && python3 -m unittest tests.test_cli_transactions -v`
Expected: `OK` (9 tests passed, 기존 동작 깨지지 않음)

- [ ] **Step 5: 사용자가 스테이징 및 커밋 진행**
---

## Task 11: CLI 계층 — import/export(CSV) + `__main__.py` + `Q2/README.md`

**Files:**
- Modify: `Q2/budget_app/cli.py` (Task 10 파일에 추가/수정)
- Create: `Q2/budget_app/__main__.py`
- Create: `Q2/tests/test_cli_import_export.py`
- Create: `Q2/README.md`

**Interfaces:**
- Consumes: `Context` (Task 9), `tests.cli_test_utils.CliTestCase` (Task 9 — 그대로 import해서 재사용), `TransactionService.{add,search}`, `TransactionRepository.iter_transactions` (Task 4/7/8)
- Produces: `cmd_import`, `cmd_export` — `(args, ctx) -> int`
- Produces: `CSV_FIELDS = ["date", "type", "category", "amount", "memo", "tags"]` (Q2.md 143-151행 고정 스키마)
- `build_parser()`에 `import --from`, `export --out --month --from --to` 추가
- `Q2/budget_app/__main__.py`: `sys.exit(cli.main())`

- [ ] **Step 1: 실패하는 테스트 작성 — `Q2/tests/test_cli_import_export.py`**

```python
import csv
import unittest
from pathlib import Path

from budget_app.exceptions import EXIT_OK, EXIT_USER_ERROR
from tests.cli_test_utils import CliTestCase


class TestCmdImport(CliTestCase):
    def test_import_adds_valid_rows_and_skips_invalid(self):
        csv_path = Path(self._tmpdir.name) / "import.csv"
        csv_path.write_text(
            "date,type,category,amount,memo,tags\n"
            "2024-01-15,expense,food,15000,점심,meal\n"
            "2024-01-16,expense,ghost-category,5000,,\n"
            "2024-01-17,income,etc,100000,,\n",
            encoding="utf-8",
        )
        code, output = self.run_cli("import", "--from", str(csv_path))
        self.assertEqual(code, EXIT_OK)
        self.assertIn("[완료] imported=2, skipped=1", output)


class TestCmdExport(CliTestCase):
    def test_export_requires_month_or_range(self):
        code, output = self.run_cli("export", "--out", str(Path(self._tmpdir.name) / "out.csv"))
        self.assertEqual(code, EXIT_USER_ERROR)

    def test_export_writes_csv_with_header_and_matching_rows(self):
        self.add_transaction("2024-01-15", "expense", "food", 15000, memo="점심", tags="meal")
        self.add_transaction("2024-02-01", "expense", "rent", 150000)
        out_path = Path(self._tmpdir.name) / "out.csv"

        code, output = self.run_cli("export", "--out", str(out_path), "--month", "2024-01")

        self.assertEqual(code, EXIT_OK)
        self.assertIn("[완료]", output)
        self.assertIn("(1 records)", output)
        with open(out_path, encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        self.assertEqual(rows[0], ["date", "type", "category", "amount", "memo", "tags"])
        self.assertEqual(rows[1], ["2024-01-15", "expense", "food", "15000", "점심", "meal"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `cd Q2 && python3 -m unittest tests.test_cli_import_export -v`
Expected: FAIL with `error: argument command: invalid choice: 'import'`

- [ ] **Step 3: `Q2/budget_app/cli.py` 수정**

파일 맨 위 `import argparse` 다음 줄에 `import csv` 추가. `cmd_category_remove` 함수 뒤, `COMMAND_HANDLERS` 선언 앞에 추가:

```python
CSV_FIELDS = ["date", "type", "category", "amount", "memo", "tags"]


@handle_errors
@log_call
@measure_time
def cmd_import(args: argparse.Namespace, ctx: Context) -> int:
    imported = 0
    skipped = 0
    with open(args.csv_from, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                tags = _read_tags(row.get("tags") or "")
                ctx.transaction_service.add(
                    date=row["date"], type=row["type"], category=row["category"],
                    amount=int(row["amount"]), memo=(row.get("memo") or None), tags=tags,
                )
                imported += 1
            except (ValidationError, KeyError, ValueError):
                skipped += 1
    print(f"[완료] imported={imported}, skipped={skipped}")
    return EXIT_OK


@handle_errors
@log_call
@measure_time
def cmd_export(args: argparse.Namespace, ctx: Context) -> int:
    if not args.month and not (args.date_from or args.date_to):
        raise ValidationError("export 조건이 필요합니다", "--month 또는 --from/--to 중 하나를 지정하세요")
    if args.month:
        rows = [t for t in ctx.transaction_repo.iter_transactions() if t.date.startswith(args.month)]
    else:
        rows = ctx.transaction_service.search(date_from=args.date_from, date_to=args.date_to)
    rows.sort(key=lambda t: (t.date, t.id))
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_FIELDS)
        for t in rows:
            writer.writerow([t.date, t.type, t.category, t.amount, t.memo or "", ",".join(t.tags)])
    print(f"[완료] {args.out} ({len(rows)} records)")
    return EXIT_OK
```

`COMMAND_HANDLERS`에 두 줄 추가:

```python
    "import": cmd_import,
    "export": cmd_export,
```

`build_parser()`의 `return parser` 바로 앞에 추가:

```python
    p_import = sub.add_parser("import")
    p_import.add_argument("--from", dest="csv_from", required=True)

    p_export = sub.add_parser("export")
    p_export.add_argument("--out", required=True)
    p_export.add_argument("--month")
    p_export.add_argument("--from", dest="date_from")
    p_export.add_argument("--to", dest="date_to")
```

- [ ] **Step 4: `Q2/budget_app/__main__.py` 작성**

```python
import sys

from budget_app.cli import main

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `cd Q2 && python3 -m unittest tests.test_cli_import_export -v`
Expected: `OK` (3 tests passed)

Run (전체 회귀 확인): `cd Q2 && python3 -m unittest discover -s tests -v`
Expected: 모든 테스트 `OK` (Task 1~11 누적 약 93개)

- [ ] **Step 6: 엔드투엔드 수동 스모크 테스트**

```bash
cd Q2 && python3 -m budget_app --help
cd Q2 && python3 -m budget_app category list
cd Q2 && python3 -m budget_app budget set --month 2024-01 --amount 500000
cd Q2 && printf '%s\n' "2024-01-15" "expense" "food" "15000" "점심" "meal" | python3 -m budget_app add
cd Q2 && python3 -m budget_app summary --month 2024-01
```

Expected: `--help`가 10개 서브커맨드를 보여주고, 나머지 명령이 `[오류]` 없이 정상 동작하며 `./data/{transactions,categories,budgets}.jsonl`과 `./logs/app.log`가 생성된다.

- [ ] **Step 7: `Q2/README.md` 작성**

```markdown
# 파일 기반 가계부 콘솔 프로그램 (budget_app)

학습용 과제(Q2) — 제너레이터 스트리밍, 데코레이터 분리, JSONL 영구 저장, 타입 힌트를 적용한
4계층(CLI/Service/Repository/Model) 구조의 콘솔 가계부. 설계 배경은
`../docs/superpowers/specs/2026-06-23-budget-app-architecture-design.md` 참고.

## 실행 방법

```bash
cd Q2
python3 -m budget_app --help
python3 -m budget_app add
python3 -m budget_app list --limit 10
python3 -m budget_app summary --month 2024-01 --top 3
```

기본 데이터 폴더는 `./data`이며 `--data-dir <경로>`로 변경할 수 있습니다.

## 저장 파일 위치/형식

- `data/transactions.jsonl`, `data/categories.jsonl`, `data/budgets.jsonl` — 한 줄에 JSON 객체 하나(JSONL)
- `logs/app.log` — 데코레이터가 기록하는 실행 로그(호출 인자, 소요 시간, 예외 스택트레이스)

## 주요 명령 예시

```bash
python3 -m budget_app add
python3 -m budget_app list --limit 5
python3 -m budget_app search --category food --from 2024-01-01 --to 2024-01-31
python3 -m budget_app update --id TX-000001 --amount 20000
python3 -m budget_app delete --id TX-000001
python3 -m budget_app category add
python3 -m budget_app category remove --name food --reassign-to etc
python3 -m budget_app budget set --month 2024-01 --amount 500000
python3 -m budget_app import --from import.csv
python3 -m budget_app export --out export.csv --month 2024-01
```

## import/export CSV 스키마

| column | required | 설명 |
| --- | --- | --- |
| date | Y | YYYY-MM-DD |
| type | Y | income / expense |
| category | Y | 등록된 카테고리 |
| amount | Y | 양수 정수 |
| memo | N | 문자열 |
| tags | N | 쉼표(,) 구분 문자열 |

공통: UTF-8, 헤더 포함. `import`는 행 단위로 검증하며 유효하지 않은 행은 건너뛰고 계속 진행합니다
(`imported`/`skipped` 건수를 출력). `export`는 `--month` 또는 `--from`/`--to` 중 최소 하나가 필요합니다.
```

- [ ] **Step 8: 사용자가 스테이징 및 커밋**