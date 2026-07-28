
from typing import Any, List, Optional

from mini_redis.doubly_linked_list import (
    DoublyLinkedList,
    DoublyLinkedListNode,
)


class HashEntry:
    """체이닝 노드에 저장되는 키와 값의 묶음."""

    def __init__(self, key: str, value: Any) -> None:
        self.key = key
        self.value = value


class HashMap:
    """키를 저장하는 체이닝 방식 해시맵."""

    _MAX_LOAD_FACTOR = 0.75

    def __init__(self, initial_capacity: int = 8) -> None:
        if initial_capacity <= 0:
            raise ValueError("initial_capacity must be greater than zero")

        self._capacity = initial_capacity
        self._size = 0
        self._buckets: List[Optional[DoublyLinkedList]] = [
            None
        ] * self._capacity

    def _hash(self, key: str) -> int:
        """문자열의 UTF-8 바이트를 직접 순회해 버킷 인덱스를 만든다."""
        hash_value = 0
        for byte in key.encode("utf-8"):
            hash_value = (hash_value * 31 + byte) % self._capacity
        return hash_value

    def _find_node(
        self, key: str
    ) -> Optional[DoublyLinkedListNode]:
        """키가 들어 있는 체이닝 노드를 찾고 없으면 None을 반환한다."""
        bucket = self._buckets[self._hash(key)]
        if bucket is None:
            return None

        current = bucket.head.next
        while current is not None and current is not bucket.tail:
            entry = current.data
            if entry.key == key:
                return current
            current = current.next
        return None

    def _insert_without_resize(self, entry: HashEntry) -> None:
        """크기와 로드 팩터 검사 없이 엔트리를 현재 버킷에 삽입한다."""
        index = self._hash(entry.key)
        bucket = self._buckets[index]
        if bucket is None:
            bucket = DoublyLinkedList()
            self._buckets[index] = bucket
        bucket.insert_back(entry)

    def _resize(self, new_capacity: int) -> None:
        """버킷 수를 늘리고 기존 엔트리를 새 인덱스로 재배치한다."""
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._buckets = [None] * self._capacity

        for bucket in old_buckets:
            if bucket is None:
                continue

            current = bucket.head.next
            while current is not None and current is not bucket.tail:
                entry = current.data
                self._insert_without_resize(entry)
                current = current.next

    def put(self, key: str, value: Any) -> None:
        """키를 새로 삽입하거나 기존 키의 값만 갱신한다."""
        node = self._find_node(key)
        if node is not None:
            node.data.value = value
            return

        next_load_factor = (self._size + 1) / self._capacity
        if next_load_factor > self._MAX_LOAD_FACTOR:
            self._resize(self._capacity * 2)

        self._insert_without_resize(HashEntry(key, value))
        self._size += 1

    def get(self, key: str) -> Any:
        """키의 값을 반환하며 키가 없으면 None을 반환한다."""
        node = self._find_node(key)
        if node is None:
            return None
        return node.data.value

    def remove(self, key: str) -> bool:
        """키를 삭제하고 실제 삭제 여부를 반환한다."""
        node = self._find_node(key)
        if node is None:
            return False

        index = self._hash(key)
        bucket = self._buckets[index]
        if bucket is None:
            raise RuntimeError("hash map invariant is broken")

        bucket.remove_node(node)
        self._size -= 1
        if bucket.size == 0:
            self._buckets[index] = None
        return True

    def contains(self, key: str) -> bool:
        """값이 None이더라도 키가 실제로 존재하는지 확인한다."""
        return self._find_node(key) is not None

    def keys(self) -> List[str]:
        """저장된 모든 키를 순서 보장 없이 반환한다."""
        result = []
        for bucket in self._buckets:
            if bucket is None:
                continue

            current = bucket.head.next
            while current is not None and current is not bucket.tail:
                result.append(current.data.key)
                current = current.next
        return result

    def size(self) -> int:
        """현재 저장된 엔트리 수를 O(1)에 반환한다."""
        return self._size
