"""
거래(Transaction) 관련 시나리오 테스트

Service 계층 직접 호출 + CLI 명령 양쪽으로 커버.
각 시나리오는 실제 사용 흐름을 모방한다.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from budget_app.exceptions import EXIT_OK, EXIT_USER_ERROR, NotFoundError, ValidationError
from budget_app.repository import CategoryRepository, TransactionRepository
from budget_app.services import CategoryService, TransactionService
from tests.cli_test_utils import CliTestCase


# ---------------------------------------------------------------------------
# Service 계층 시나리오
# ---------------------------------------------------------------------------

class _ServiceBase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        base = Path(self._tmpdir.name)
        self.tx_repo = TransactionRepository(base / "transactions.jsonl")
        self.cat_service = CategoryService(CategoryRepository(base / "categories.jsonl"))
        self.svc = TransactionService(self.tx_repo, self.cat_service)


class TestTransactionLifecycle(_ServiceBase):
    """add → get → update → delete 전체 생명주기"""

    def test_full_lifecycle(self):
        t = self.svc.add(date="2024-03-01", type="expense", category="food", amount=12000, memo="커피")
        self.assertEqual(t.id, "TX-000001")

        fetched = self.svc.get(t.id)
        self.assertEqual(fetched.memo, "커피")

        updated = self.svc.update(t.id, amount=15000, memo="커피+케이크")
        self.assertEqual(updated.amount, 15000)
        self.assertEqual(updated.memo, "커피+케이크")
        self.assertEqual(updated.date, "2024-03-01")  # 변경하지 않은 필드 유지

        self.svc.delete(t.id)
        with self.assertRaises(NotFoundError):
            self.svc.get(t.id)

    def test_id_sequence_is_gap_free_after_delete(self):
        t1 = self.svc.add(date="2024-01-01", type="income", category="etc", amount=1000)
        t2 = self.svc.add(date="2024-01-02", type="expense", category="food", amount=500)
        self.svc.delete(t1.id)
        # 다음 id는 gap 없이 TX-000003
        t3 = self.svc.add(date="2024-01-03", type="expense", category="food", amount=300)
        self.assertEqual(t3.id, "TX-000003")
        self.assertEqual(t2.id, "TX-000002")


class TestTransactionAddValidation(_ServiceBase):
    """add 시 입력 검증 규칙"""

    def test_add_rejects_date_format_slash(self):
        with self.assertRaises(ValidationError) as ctx:
            self.svc.add(date="2024/01/15", type="expense", category="food", amount=1000)
        self.assertIn("2024/01/15", ctx.exception.message)

    def test_add_rejects_date_format_no_padding(self):
        with self.assertRaises(ValidationError):
            self.svc.add(date="2024-1-5", type="expense", category="food", amount=1000)

    def test_add_rejects_impossible_date_feb29_non_leap(self):
        with self.assertRaises(ValidationError):
            self.svc.add(date="2023-02-29", type="expense", category="food", amount=1000)

    def test_add_accepts_leap_year_feb29(self):
        t = self.svc.add(date="2024-02-29", type="expense", category="food", amount=1000)
        self.assertEqual(t.date, "2024-02-29")

    def test_add_rejects_amount_zero(self):
        with self.assertRaises(ValidationError) as ctx:
            self.svc.add(date="2024-01-01", type="expense", category="food", amount=0)
        self.assertIn("양수", ctx.exception.message)

    def test_add_rejects_amount_negative(self):
        with self.assertRaises(ValidationError):
            self.svc.add(date="2024-01-01", type="expense", category="food", amount=-500)

    def test_add_rejects_unknown_type(self):
        with self.assertRaises(ValidationError) as ctx:
            self.svc.add(date="2024-01-01", type="transfer", category="food", amount=1000)
        self.assertIn("transfer", ctx.exception.message)

    def test_add_rejects_unregistered_category(self):
        with self.assertRaises(ValidationError) as ctx:
            self.svc.add(date="2024-01-01", type="expense", category="ghost", amount=1000)
        self.assertIn("ghost", ctx.exception.message)

    def test_add_accepts_large_amount(self):
        t = self.svc.add(date="2024-01-01", type="income", category="etc", amount=100_000_000)
        self.assertEqual(t.amount, 100_000_000)

    def test_add_accepts_boundary_date_dec31(self):
        t = self.svc.add(date="2024-12-31", type="expense", category="food", amount=1000)
        self.assertEqual(t.date, "2024-12-31")


class TestTransactionUpdateValidation(_ServiceBase):
    """update 시 검증 — 변경 필드만 재검증, 나머지는 기존 값 유지"""

    def setUp(self):
        super().setUp()
        self.t = self.svc.add(date="2024-01-15", type="expense", category="food", amount=1000)

    def test_update_only_amount_keeps_other_fields(self):
        updated = self.svc.update(self.t.id, amount=2000)
        self.assertEqual(updated.amount, 2000)
        self.assertEqual(updated.type, "expense")
        self.assertEqual(updated.category, "food")
        self.assertEqual(updated.date, "2024-01-15")

    def test_update_category_to_unregistered_raises(self):
        with self.assertRaises(ValidationError):
            self.svc.update(self.t.id, category="nonexistent")

    def test_update_type_to_invalid_raises(self):
        with self.assertRaises(ValidationError):
            self.svc.update(self.t.id, type="wire")

    def test_update_amount_to_zero_raises(self):
        with self.assertRaises(ValidationError):
            self.svc.update(self.t.id, amount=0)

    def test_update_date_to_impossible_raises(self):
        with self.assertRaises(ValidationError):
            self.svc.update(self.t.id, date="2024-13-01")

    def test_update_memo_to_empty_string(self):
        self.svc.update(self.t.id, memo="원래 메모")
        updated = self.svc.update(self.t.id, memo="")
        self.assertEqual(updated.memo, "")

    def test_update_tags_replaces_entire_list(self):
        self.svc.update(self.t.id, tags=["a", "b"])
        updated = self.svc.update(self.t.id, tags=["c"])
        self.assertEqual(updated.tags, ["c"])

    def test_update_missing_id_raises_not_found(self):
        with self.assertRaises(NotFoundError):
            self.svc.update("TX-999999", amount=9999)


class TestTransactionListAndSearch(_ServiceBase):
    """list/search 정렬·필터·조합 검증"""

    def setUp(self):
        super().setUp()
        self.cat_service.add("hobby")
        self.svc.add(date="2024-01-10", type="income", category="etc", amount=3000000, tags=["salary"])
        self.svc.add(date="2024-01-12", type="expense", category="transport", amount=20000)
        self.svc.add(date="2024-01-14", type="expense", category="food", amount=45000, memo="회식", tags=["meal", "team"])
        self.svc.add(date="2024-01-14", type="expense", category="hobby", amount=30000, memo="게임")
        self.svc.add(date="2024-02-01", type="expense", category="rent", amount=150000)

    def test_list_newest_first(self):
        rows = self.svc.list(limit=10)
        dates = [t.date for t in rows]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_list_same_date_id_desc(self):
        rows = self.svc.list(limit=10)
        jan14 = [t for t in rows if t.date == "2024-01-14"]
        self.assertEqual(jan14[0].id, "TX-000004")
        self.assertEqual(jan14[1].id, "TX-000003")

    def test_list_limit_zero_returns_empty(self):
        self.assertEqual(self.svc.list(limit=0), [])

    def test_list_limit_larger_than_total(self):
        rows = self.svc.list(limit=100)
        self.assertEqual(len(rows), 5)

    def test_search_by_type_income(self):
        rows = self.svc.search(type="income")
        self.assertTrue(all(t.type == "income" for t in rows))
        self.assertEqual(len(rows), 1)

    def test_search_by_date_range_exclusive_boundary(self):
        rows = self.svc.search(date_from="2024-01-12", date_to="2024-01-14")
        dates = {t.date for t in rows}
        self.assertIn("2024-01-12", dates)
        self.assertIn("2024-01-14", dates)
        self.assertNotIn("2024-01-10", dates)
        self.assertNotIn("2024-02-01", dates)

    def test_search_query_against_no_memo_returns_empty(self):
        rows = self.svc.search(query="아무개")
        self.assertEqual(rows, [])

    def test_search_query_partial_match(self):
        rows = self.svc.search(query="게임")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].category, "hobby")

    def test_search_tag_one_of_multiple_tags(self):
        rows = self.svc.search(tag="team")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].memo, "회식")

    def test_search_combined_filters_and_logic(self):
        rows = self.svc.search(date_from="2024-01-01", date_to="2024-01-31", type="expense", category="food")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].category, "food")

    def test_search_no_match_returns_empty_list(self):
        rows = self.svc.search(category="rent", type="income")
        self.assertEqual(rows, [])


class TestTransactionSummary(_ServiceBase):
    """summary 계산 — 수입/지출/잔액/top N 카테고리"""

    def setUp(self):
        super().setUp()
        self.svc.add(date="2024-01-10", type="income", category="etc", amount=3_000_000)
        self.svc.add(date="2024-01-12", type="expense", category="transport", amount=20_000)
        self.svc.add(date="2024-01-14", type="expense", category="food", amount=45_000)
        self.svc.add(date="2024-01-14", type="expense", category="rent", amount=150_000)
        self.svc.add(date="2024-02-01", type="expense", category="rent", amount=150_000)

    def test_summary_totals_correct(self):
        r = self.svc.summary("2024-01")
        self.assertEqual(r["total_income"], 3_000_000)
        self.assertEqual(r["total_expense"], 215_000)
        self.assertEqual(r["balance"], 2_785_000)

    def test_summary_has_data_true_when_transactions_exist(self):
        r = self.svc.summary("2024-01")
        self.assertTrue(r["has_data"])

    def test_summary_has_data_false_for_empty_month(self):
        r = self.svc.summary("2099-01")
        self.assertFalse(r["has_data"])
        self.assertEqual(r["total_income"], 0)
        self.assertEqual(r["total_expense"], 0)
        self.assertEqual(r["balance"], 0)
        self.assertEqual(r["top_categories"], [])

    def test_summary_top_categories_expense_only(self):
        r = self.svc.summary("2024-01", top=3)
        categories = [name for name, _ in r["top_categories"]]
        self.assertEqual(categories[0], "rent")   # 가장 큰 지출
        self.assertEqual(categories[1], "food")

    def test_summary_top_1(self):
        r = self.svc.summary("2024-01", top=1)
        self.assertEqual(len(r["top_categories"]), 1)
        self.assertEqual(r["top_categories"][0][0], "rent")

    def test_summary_income_only_month_has_no_top_categories(self):
        self.svc.add(date="2024-03-01", type="income", category="etc", amount=500_000)
        r = self.svc.summary("2024-03")
        self.assertEqual(r["top_categories"], [])
        self.assertEqual(r["total_expense"], 0)

    def test_summary_different_month_is_isolated(self):
        r_jan = self.svc.summary("2024-01")
        r_feb = self.svc.summary("2024-02")
        self.assertEqual(r_jan["total_expense"], 215_000)
        self.assertEqual(r_feb["total_expense"], 150_000)


# ---------------------------------------------------------------------------
# CLI 계층 시나리오
# ---------------------------------------------------------------------------

class TestCliTransactionScenarios(CliTestCase):
    """CLI를 통한 거래 시나리오"""

    def test_add_income_transaction(self):
        code, out = self.add_transaction("2024-05-01", "income", "etc", 2000000)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("TX-000001", out)

    def test_add_multiple_ids_increment(self):
        self.add_transaction("2024-01-01", "expense", "food", 1000)
        self.add_transaction("2024-01-02", "expense", "food", 2000)
        code, out = self.add_transaction("2024-01-03", "income", "etc", 3000)
        self.assertIn("TX-000003", out)

    def test_list_after_multiple_adds_shows_newest_first(self):
        self.add_transaction("2024-01-01", "expense", "food", 1000)
        self.add_transaction("2024-01-31", "income", "etc", 999999)
        _, out = self.run_cli("list", "--limit", "5")
        lines = [l for l in out.splitlines() if l.startswith("TX-")]
        self.assertTrue(lines[0].startswith("TX-000002"))

    def test_search_combined_category_and_type(self):
        self.add_transaction("2024-01-10", "expense", "food", 5000)
        self.add_transaction("2024-01-10", "income", "food", 10000)  # food는 없지만 etc로 대체
        self.add_transaction("2024-01-10", "expense", "transport", 3000)
        code, out = self.run_cli("search", "--category", "food", "--type", "expense")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("TX-000001", out)
        self.assertNotIn("TX-000003", out)

    def test_update_then_list_reflects_change(self):
        self.add_transaction("2024-02-01", "expense", "food", 10000)
        self.run_cli("update", "--id", "TX-000001", "--amount", "99999", "--memo", "updated")
        _, out = self.run_cli("list")
        self.assertIn("99999", out)

    def test_delete_then_list_shows_empty(self):
        self.add_transaction("2024-01-01", "expense", "food", 1000)
        self.run_cli("delete", "--id", "TX-000001")
        _, out = self.run_cli("list")
        self.assertIn("거래 내역이 없습니다", out)

    def test_search_by_date_range_via_cli(self):
        self.add_transaction("2024-01-05", "expense", "food", 1000)
        self.add_transaction("2024-01-20", "expense", "food", 2000)
        self.add_transaction("2024-02-01", "expense", "transport", 3000)
        code, out = self.run_cli("search", "--from", "2024-01-01", "--to", "2024-01-31")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("TX-000001", out)
        self.assertIn("TX-000002", out)
        self.assertNotIn("TX-000003", out)

    def test_update_nonexistent_id_reports_error(self):
        code, out = self.run_cli("update", "--id", "TX-999999", "--amount", "1000")
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류]", out)

    def test_delete_nonexistent_id_reports_error(self):
        code, out = self.run_cli("delete", "--id", "TX-000000")
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류]", out)


if __name__ == "__main__":
    unittest.main()
