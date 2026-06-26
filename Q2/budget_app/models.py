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
