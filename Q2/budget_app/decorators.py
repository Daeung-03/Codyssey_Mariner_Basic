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
