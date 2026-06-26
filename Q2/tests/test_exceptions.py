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
