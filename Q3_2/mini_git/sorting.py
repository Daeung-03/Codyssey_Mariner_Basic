"""정렬 알고리즘 직접 구현 모듈.

sorted(), list.sort() 사용 금지 제약에 따라 Merge Sort를 직접 구현한다.
안정 정렬, O(n log n) 보장.
"""

from __future__ import annotations

from typing import Any, Callable


def merge_sort(items: list[Any], key: Callable[[Any], Any] | None = None) -> list[Any]:
    """Merge Sort로 리스트를 오름차순 정렬하여 새 리스트를 반환한다.

    Args:
        items: 정렬할 리스트.
        key: 비교 기준을 추출하는 함수. None이면 원소 자체를 비교.

    Returns:
        정렬된 새 리스트 (원본 변경 없음).
    """
    if len(items) <= 1:
        return list(items)

    mid = len(items) // 2
    left = merge_sort(items[:mid], key=key)
    right = merge_sort(items[mid:], key=key)

    return _merge(left, right, key=key)


def _merge(
    left: list[Any],
    right: list[Any],
    key: Callable[[Any], Any] | None = None,
) -> list[Any]:
    """두 정렬된 리스트를 병합한다."""
    result: list[Any] = []
    i = j = 0

    while i < len(left) and j < len(right):
        left_key = key(left[i]) if key else left[i]
        right_key = key(right[j]) if key else right[j]

        if left_key <= right_key:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result
