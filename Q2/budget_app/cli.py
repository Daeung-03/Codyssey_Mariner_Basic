from __future__ import annotations

import argparse
import csv
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


CSV_FIELDS = ["date", "type", "category", "amount", "memo", "tags"]


@handle_errors
@log_call
@measure_time
def cmd_import(args: argparse.Namespace, ctx: Context) -> int:
    imported = 0
    skipped = 0
    # _next_id() 파일 전체 스캔을 루프 밖으로 한 번만 수행
    seq = int(ctx.transaction_service._next_id().split("-")[1])
    with open(args.csv_from, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                tags = _read_tags(row.get("tags") or "")
                ctx.transaction_service.add(
                    date=row["date"], type=row["type"], category=row["category"],
                    amount=int(row["amount"]), memo=(row.get("memo") or None), tags=tags,
                    _id=f"TX-{seq:06d}",
                )
                seq += 1
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


COMMAND_HANDLERS: dict[str, Callable[[argparse.Namespace, Context], int]] = {
    "add": cmd_add,
    "list": cmd_list,
    "search": cmd_search,
    "update": cmd_update,
    "delete": cmd_delete,
    "summary": cmd_summary,
    "import": cmd_import,
    "export": cmd_export,
}

BUDGET_HANDLERS: dict[str, Callable[[argparse.Namespace, Context], int]] = {
    "set": cmd_budget_set,
}

CATEGORY_HANDLERS: dict[str, Callable[[argparse.Namespace, Context], int]] = {
    "add": cmd_category_add,
    "list": cmd_category_list,
    "remove": cmd_category_remove,
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

    p_import = sub.add_parser("import")
    p_import.add_argument("--from", dest="csv_from", required=True)

    p_export = sub.add_parser("export")
    p_export.add_argument("--out", required=True)
    p_export.add_argument("--month")
    p_export.add_argument("--from", dest="date_from")
    p_export.add_argument("--to", dest="date_to")

    return parser


def dispatch(args: argparse.Namespace, ctx: Context) -> int:
    if args.command == "budget":
        return BUDGET_HANDLERS[args.budget_command](args, ctx)
    if args.command == "category":
        return CATEGORY_HANDLERS[args.category_command](args, ctx)
    return COMMAND_HANDLERS[args.command](args, ctx)


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
