"""배열 기반 최소 힙.

완전 이진 트리를 0-based 배열로 표현하며,
각 부모의 우선순위 값이 자식 이하가 되도록 불변식을 유지한다.
TTL 관리에서는 (expire_at, key) 튜플을 저장하여
가장 이른 만료를 루트에서 O(1)에 확인한다.
"""

from typing import Any, List


class MinHeap:
    """최소 힙 — 우선순위가 가장 낮은(작은) 요소가 루트에 위치한다."""

    def __init__(self) -> None:
        self._items: List[Any] = []

    # ─── 공개 메서드 ───

    def push(self, item: Any) -> None:
        """새 요소를 힙에 추가하고 불변식을 복구한다. O(log N)"""
        self._items.append(item)
        self._heapify_up(len(self._items) - 1)

    def pop(self) -> Any:
        """루트(최솟값)를 제거하고 반환한다. 빈 힙이면 IndexError. O(log N)"""
        if not self._items:
            raise IndexError("pop from empty heap")

        root = self._items[0]
        last = self._items.pop()

        if self._items:
            self._items[0] = last
            self._heapify_down(0)

        return root

    def peek(self) -> Any:
        """루트(최솟값)를 제거하지 않고 반환한다. 빈 힙이면 IndexError. O(1)"""
        if not self._items:
            raise IndexError("peek from empty heap")
        return self._items[0]

    def size(self) -> int:
        """현재 저장된 요소 수를 반환한다. O(1)"""
        return len(self._items)

    # ─── 내부 헬퍼 ───

    def _heapify_up(self, index: int) -> None:
        """삽입된 위치에서 루트 방향으로 올라가며 불변식을 복구한다."""
        while index > 0:
            parent = (index - 1) // 2
            if self._items[index][0] < self._items[parent][0]:
                self._items[index], self._items[parent] = (
                    self._items[parent],
                    self._items[index],
                )
                index = parent
            else:
                break

    def _heapify_down(self, index: int) -> None:
        """루트에서 리프 방향으로 내려가며 불변식을 복구한다."""
        size = len(self._items)

        while True:
            smallest = index
            left = 2 * index + 1
            right = 2 * index + 2

            if left < size and self._items[left][0] < self._items[smallest][0]:
                smallest = left
            if right < size and self._items[right][0] < self._items[smallest][0]:
                smallest = right

            if smallest == index:
                break

            self._items[index], self._items[smallest] = (
                self._items[smallest],
                self._items[index],
            )
            index = smallest
