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
