"""
카테고리(Category) 관련 시나리오 테스트

기본 카테고리 자동 생성, 추가/삭제 흐름, reassign 정책, 중복 방지 등을 검증.
"""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from budget_app.exceptions import (
    EXIT_OK,
    EXIT_USER_ERROR,
    CategoryInUseError,
    NotFoundError,
    ValidationError,
)
from budget_app.models import Category
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
        self.cat_repo = CategoryRepository(base / "categories.jsonl")
        self.tx_repo = TransactionRepository(base / "transactions.jsonl")
        self.cat_service = CategoryService(self.cat_repo)
        self.tx_service = TransactionService(self.tx_repo, self.cat_service)


class TestDefaultCategories(_ServiceBase):
    """빈 저장소에서 CategoryService 생성 시 기본 카테고리 자동 등록"""

    def test_default_categories_are_registered(self):
        names = {c.name for c in self.cat_service.list()}
        self.assertEqual(names, {"food", "transport", "rent", "etc"})

    def test_default_categories_count_is_four(self):
        self.assertEqual(len(self.cat_service.list()), 4)

    def test_existing_data_not_overwritten(self):
        # 기존 카테고리가 있으면 기본 값 삽입 안 함
        custom_repo = CategoryRepository(
            Path(self._tmpdir.name) / "custom_categories.jsonl"
        )
        custom_repo.append(Category(name="custom"))
        svc = CategoryService(custom_repo)
        names = {c.name for c in svc.list()}
        self.assertEqual(names, {"custom"})
        self.assertNotIn("food", names)


class TestCategoryAdd(_ServiceBase):
    """카테고리 추가 정책"""

    def test_add_new_category(self):
        cat = self.cat_service.add("hobby")
        self.assertEqual(cat.name, "hobby")
        self.assertTrue(self.cat_service.exists("hobby"))

    def test_add_duplicate_raises_validation_error(self):
        with self.assertRaises(ValidationError) as ctx:
            self.cat_service.add("food")
        self.assertIn("food", ctx.exception.message)

    def test_add_multiple_custom_categories(self):
        self.cat_service.add("hobby")
        self.cat_service.add("medical")
        self.cat_service.add("education")
        self.assertEqual(len(self.cat_service.list()), 7)  # 기본 4 + 3

    def test_added_category_usable_in_transaction(self):
        self.cat_service.add("hobby")
        t = self.tx_service.add(date="2024-01-01", type="expense", category="hobby", amount=5000)
        self.assertEqual(t.category, "hobby")


class TestCategoryRemove(_ServiceBase):
    """카테고리 삭제 정책 — 미사용/사용 중/재배정"""

    def test_remove_unused_category(self):
        self.cat_service.add("hobby")
        self.cat_service.remove("hobby", self.tx_repo)
        self.assertFalse(self.cat_service.exists("hobby"))

    def test_remove_nonexistent_raises_not_found(self):
        with self.assertRaises(NotFoundError) as ctx:
            self.cat_service.remove("ghost", self.tx_repo)
        self.assertIn("ghost", ctx.exception.message)

    def test_remove_in_use_without_reassign_raises(self):
        self.tx_service.add(date="2024-01-01", type="expense", category="food", amount=1000)
        with self.assertRaises(CategoryInUseError) as ctx:
            self.cat_service.remove("food", self.tx_repo)
        self.assertIn("food", ctx.exception.message)
        # 카테고리는 여전히 존재해야 함
        self.assertTrue(self.cat_service.exists("food"))

    def test_remove_in_use_with_reassign_moves_all_transactions(self):
        self.tx_service.add(date="2024-01-01", type="expense", category="food", amount=1000)
        self.tx_service.add(date="2024-01-02", type="expense", category="food", amount=2000)
        self.cat_service.remove("food", self.tx_repo, reassign_to="etc")
        rows = list(self.tx_repo.iter_transactions())
        self.assertTrue(all(t.category == "etc" for t in rows))
        self.assertFalse(self.cat_service.exists("food"))

    def test_reassign_to_nonexistent_target_raises(self):
        self.tx_service.add(date="2024-01-01", type="expense", category="food", amount=1000)
        with self.assertRaises(NotFoundError):
            self.cat_service.remove("food", self.tx_repo, reassign_to="ghost")
        # 롤백 — food는 여전히 존재
        self.assertTrue(self.cat_service.exists("food"))

    def test_remove_default_category_when_unused(self):
        self.cat_service.remove("etc", self.tx_repo)
        self.assertFalse(self.cat_service.exists("etc"))

    def test_after_reassign_new_category_reflects_in_search(self):
        self.tx_service.add(date="2024-01-01", type="expense", category="food", amount=5000)
        self.cat_service.remove("food", self.tx_repo, reassign_to="etc")
        rows = self.tx_service.search(category="etc")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].amount, 5000)


# ---------------------------------------------------------------------------
# CLI 계층 시나리오
# ---------------------------------------------------------------------------

class TestCliCategoryScenarios(CliTestCase):

    def test_category_list_shows_defaults(self):
        code, out = self.run_cli("category", "list")
        self.assertEqual(code, EXIT_OK)
        for name in ("food", "transport", "rent", "etc"):
            self.assertIn(f"- {name}", out)

    def test_category_add_via_interactive_input(self):
        with patch("builtins.input", lambda _prompt="": "healthcare"):
            code, out = self.run_cli("category", "add")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("[저장 완료] category=healthcare", out)
        _, list_out = self.run_cli("category", "list")
        self.assertIn("- healthcare", list_out)

    def test_category_add_duplicate_reports_error(self):
        with patch("builtins.input", lambda _prompt="": "food"):
            code, out = self.run_cli("category", "add")
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류]", out)
        self.assertIn("[힌트]", out)

    def test_category_remove_unused(self):
        with patch("builtins.input", lambda _prompt="": "temp"):
            self.run_cli("category", "add")
        code, out = self.run_cli("category", "remove", "--name", "temp")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("[삭제 완료] category=temp", out)

    def test_category_remove_nonexistent_reports_error(self):
        code, out = self.run_cli("category", "remove", "--name", "ghost-cat")
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류]", out)

    def test_category_remove_in_use_requires_reassign(self):
        self.add_transaction("2024-01-10", "expense", "transport", 5000)
        code, out = self.run_cli("category", "remove", "--name", "transport")
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("--reassign-to", out)

    def test_category_remove_with_reassign_and_verify_search(self):
        self.add_transaction("2024-01-10", "expense", "transport", 5000)
        code, out = self.run_cli(
            "category", "remove", "--name", "transport", "--reassign-to", "etc"
        )
        self.assertEqual(code, EXIT_OK)
        _, search_out = self.run_cli("search", "--category", "etc")
        self.assertIn("TX-000001", search_out)


if __name__ == "__main__":
    unittest.main()
