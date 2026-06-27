"""
오류 처리 시나리오 테스트

handle_errors 데코레이터 동작, 종료 코드 정책, 스택트레이스 비노출,
힌트 출력 등을 검증.
"""
import io
import logging
import unittest
from contextlib import redirect_stdout

from budget_app.decorators import handle_errors, log_call, measure_time
from budget_app.exceptions import (
    EXIT_OK,
    EXIT_SYSTEM_ERROR,
    EXIT_USER_ERROR,
    BudgetAppError,
    CategoryInUseError,
    NotFoundError,
    StorageError,
    ValidationError,
)
from tests.cli_test_utils import CliTestCase


class TestHandleErrorsPolicy(unittest.TestCase):
    """handle_errors — 오류 유형별 종료 코드·출력 정책"""

    def _run(self, func):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = func()
        return code, buf.getvalue()

    def test_success_returns_exit_ok(self):
        @handle_errors
        def fn():
            return EXIT_OK
        code, _ = self._run(fn)
        self.assertEqual(code, EXIT_OK)

    def test_validation_error_returns_exit_1(self):
        @handle_errors
        def fn():
            raise ValidationError("날짜 형식 오류", "예: 2024-01-15")
        code, out = self._run(fn)
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류] 날짜 형식 오류", out)
        self.assertIn("[힌트] 예: 2024-01-15", out)

    def test_not_found_error_returns_exit_1(self):
        @handle_errors
        def fn():
            raise NotFoundError("없는 ID")
        code, out = self._run(fn)
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류] 없는 ID", out)

    def test_category_in_use_error_returns_exit_1(self):
        @handle_errors
        def fn():
            raise CategoryInUseError("사용 중인 카테고리", "--reassign-to 지정")
        code, out = self._run(fn)
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("--reassign-to 지정", out)

    def test_storage_error_returns_exit_2(self):
        @handle_errors
        def fn():
            raise StorageError("저장 실패", "디스크 확인")
        code, out = self._run(fn)
        self.assertEqual(code, EXIT_SYSTEM_ERROR)

    def test_unexpected_exception_returns_exit_2_no_traceback(self):
        @handle_errors
        def fn():
            raise RuntimeError("내부 버그")
        buf = io.StringIO()
        with self.assertLogs("budget_app", level="ERROR"):
            with redirect_stdout(buf):
                code = fn()
        self.assertEqual(code, EXIT_SYSTEM_ERROR)
        self.assertNotIn("Traceback", buf.getvalue())
        self.assertIn("[오류]", buf.getvalue())

    def test_error_without_hint_does_not_print_hint_line(self):
        @handle_errors
        def fn():
            raise NotFoundError("없는 항목")  # hint 없음
        _, out = self._run(fn)
        self.assertNotIn("[힌트]", out)

    def test_stacking_order_handle_errors_wraps_log_call_wraps_measure_time(self):
        @handle_errors
        @log_call
        @measure_time
        def fn():
            raise ValidationError("검증 실패", "힌트 메시지")
        buf = io.StringIO()
        with self.assertLogs("budget_app", level="INFO"):
            with redirect_stdout(buf):
                code = fn()
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류] 검증 실패", buf.getvalue())


class TestExitCodeConstants(unittest.TestCase):
    def test_exit_ok_is_zero(self):
        self.assertEqual(EXIT_OK, 0)

    def test_exit_user_error_is_one(self):
        self.assertEqual(EXIT_USER_ERROR, 1)

    def test_exit_system_error_is_two(self):
        self.assertEqual(EXIT_SYSTEM_ERROR, 2)


class TestCliErrorOutput(CliTestCase):
    """CLI 명령에서 오류 발생 시 [오류]/[힌트] 형식으로 출력"""

    def test_add_invalid_date_prints_error_and_hint(self):
        code, out = self.add_transaction("2024/01/15", "expense", "food", 1000)
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류]", out)
        self.assertIn("[힌트]", out)

    def test_update_missing_fields_prints_error(self):
        self.add_transaction("2024-01-01", "expense", "food", 1000)
        code, out = self.run_cli("update", "--id", "TX-000001")
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류]", out)

    def test_delete_nonexistent_prints_error(self):
        code, out = self.run_cli("delete", "--id", "TX-999999")
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[오류]", out)

    def test_category_remove_in_use_prints_reassign_hint(self):
        self.add_transaction("2024-01-01", "expense", "food", 1000)
        code, out = self.run_cli("category", "remove", "--name", "food")
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("--reassign-to", out)

    def test_export_no_filter_prints_error_and_hint(self):
        import tempfile
        from pathlib import Path
        out_path = Path(self._tmpdir.name) / "x.csv"
        code, out = self.run_cli("export", "--out", str(out_path))
        self.assertEqual(code, EXIT_USER_ERROR)
        self.assertIn("[힌트]", out)


if __name__ == "__main__":
    logging.getLogger("budget_app").setLevel(logging.INFO)
    unittest.main()
