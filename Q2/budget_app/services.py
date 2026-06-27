from __future__ import annotations

import re
from dataclasses import replace as dc_replace
from datetime import date as date_cls

from budget_app.exceptions import CategoryInUseError, NotFoundError, ValidationError
from budget_app.models import Budget, Category, Transaction
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
        _id: str | None = None,
    ) -> Transaction:
        self._validate_fields(date, type, category, amount)
        transaction = Transaction(
            id=_id if _id is not None else self._next_id(),
            type=type, date=date, amount=amount,
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
        has_data = False
        total_income = 0
        total_expense = 0
        by_category: dict[str, int] = {}
        for t in self.repo.iter_transactions():
            if not t.date.startswith(month):
                continue
            has_data = True
            if t.type == "income":
                total_income += t.amount
            else:
                total_expense += t.amount
                by_category[t.category] = by_category.get(t.category, 0) + t.amount
        top_categories = sorted(by_category.items(), key=lambda kv: kv[1], reverse=True)[:top]
        return {
            "has_data": has_data,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "top_categories": top_categories,
        }
