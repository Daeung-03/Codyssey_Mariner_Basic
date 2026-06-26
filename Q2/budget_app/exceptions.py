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
