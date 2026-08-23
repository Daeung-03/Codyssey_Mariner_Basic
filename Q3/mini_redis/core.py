"""MiniRedis 핵심 엔진.

CacheEntry, OutOfMemoryError, MiniRedis 클래스를 포함한다.
커스텀 HashMap, DoublyLinkedList, MinHeap을 조합하여
LRU 퇴출, TTL lazy deletion, 메모리 제한을 구현한다.
"""

import math
import time
from typing import Any, Callable, List, Optional, Tuple

from mini_redis.doubly_linked_list import DoublyLinkedList, DoublyLinkedListNode
from mini_redis.hash_map import HashMap
from mini_redis.min_heap import MinHeap


class CacheEntry:
    """LRU 노드의 data에 저장되는 키·값 묶음."""

    def __init__(self, key: str, value: str) -> None:
        self.key = key
        self.value = value


class OutOfMemoryError(Exception):
    """단일 엔트리가 maxmemory를 초과할 때 발생한다."""
    pass


class MiniRedis:
    """Redis 스타일 인메모리 Key-Value 저장소.

    Args:
        clock: 현재 시각을 반환하는 호출 가능 객체. 기본값은 time.monotonic.
               테스트에서 가짜 시계를 주입하여 TTL을 결정적으로 검증한다.
    """

    def __init__(self, clock: Optional[Callable[[], float]] = None) -> None:
        # 핵심 상태
        self._data_map = HashMap()          # key -> LRU 노드 참조
        self._lru_list = DoublyLinkedList()  # 앞=최근, 뒤=오래된
        self._expiry_map = HashMap()         # key -> expire_at (현재 유효)
        self._expiry_heap = MinHeap()        # (expire_at, key)

        # 메모리 관리
        self._used_memory: int = 0
        self._maxmemory: int = 0            # 0 = 무제한
        self._evicted_keys: int = 0

        # 시계
        self._clock = clock if clock is not None else time.monotonic

    # ═══════════════════════════════════════════════════════
    # 내부 헬퍼
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def _entry_size(key: str, value: str) -> int:
        """키와 값의 UTF-8 바이트 합을 반환한다."""
        return len(key.encode("utf-8")) + len(value.encode("utf-8"))

    def _delete_key(self, key: str, count_as_eviction: bool = False) -> bool:
        """키를 모든 구조에서 제거한다. 없으면 False."""
        node: Optional[DoublyLinkedListNode] = self._data_map.get(key)
        if node is None:
            return False

        entry: CacheEntry = node.data
        self._used_memory -= self._entry_size(entry.key, entry.value)

        self._data_map.remove(key)
        self._lru_list.remove_node(node)
        self._expiry_map.remove(key)
        # 힙의 과거 예약은 lazy deletion으로 남긴다

        if count_as_eviction:
            self._evicted_keys += 1

        return True

    def _purge_expired(self) -> None:
        """만료된 키를 힙에서 정리한다."""
        now = self._clock()

        while self._expiry_heap.size() > 0:
            expire_at, key = self._expiry_heap.peek()

            # TTL 해시맵에 키가 없으면 TTL이 취소된 오래된 항목
            current_expire: Optional[float] = self._expiry_map.get(key)
            if current_expire is None:
                self._expiry_heap.pop()
                continue

            # 현재 expire_at과 일치하지 않으면 갱신 전 오래된 항목
            if current_expire != expire_at:
                self._expiry_heap.pop()
                continue

            # 유효 항목이지만 아직 만료 전이면 중단
            if expire_at > now:
                break

            # 유효하고 만료됨 -> 실제 삭제
            self._expiry_heap.pop()
            self._delete_key(key)

    def _evict_lru(self) -> None:
        """used_memory <= maxmemory가 될 때까지 LRU 뒤쪽부터 퇴출한다."""
        while (
            self._maxmemory > 0
            and self._used_memory > self._maxmemory
            and self._lru_list.size > 0
        ):
            tail_node = self._lru_list.tail.prev
            if tail_node is None or tail_node is self._lru_list.head:
                break
            entry: CacheEntry = tail_node.data
            self._delete_key(entry.key, count_as_eviction=True)

    # ═══════════════════════════════════════════════════════
    # String 명령 (6개)
    # ═══════════════════════════════════════════════════════

    def set(self, key: str, value: str) -> bool:
        """SET key value. 성공 시 True, 단일 엔트리 OOM 시 예외."""
        self._purge_expired()

        new_size = self._entry_size(key, value)

        # 단일 엔트리 OOM 검사
        if self._maxmemory > 0 and new_size > self._maxmemory:
            raise OutOfMemoryError()

        existing_node: Optional[DoublyLinkedListNode] = self._data_map.get(key)

        if existing_node is not None:
            # 기존 키 덮어쓰기
            old_entry: CacheEntry = existing_node.data
            old_size = self._entry_size(old_entry.key, old_entry.value)

            # OOM 검사: 덮어쓴 후에도 이 엔트리 자체가 제한 초과면 거부
            # (단일 엔트리 검사는 이미 위에서 했으므로 여기선 값만 교체)
            old_entry.value = value
            self._used_memory += new_size - old_size
            self._lru_list.move_to_front(existing_node)

            # 기존 TTL 제거
            self._expiry_map.remove(key)
        else:
            # 새 키 삽입
            entry = CacheEntry(key, value)
            node = self._lru_list.insert_front(entry)
            self._data_map.put(key, node)
            self._used_memory += new_size

        # LRU 퇴출
        self._evict_lru()

        return True

    def get(self, key: str) -> Optional[str]:
        """GET key. 값 또는 None."""
        self._purge_expired()

        node: Optional[DoublyLinkedListNode] = self._data_map.get(key)
        if node is None:
            return None

        self._lru_list.move_to_front(node)
        entry: CacheEntry = node.data
        return entry.value

    def delete(self, key: str) -> int:
        """DEL key. 삭제 성공 1, 없으면 0."""
        self._purge_expired()
        return 1 if self._delete_key(key) else 0

    def exists(self, key: str) -> int:
        """EXISTS key. 존재 1, 없으면 0."""
        self._purge_expired()
        return 1 if self._data_map.contains(key) else 0

    def dbsize(self) -> int:
        """DBSIZE. 현재 유효 키 수."""
        self._purge_expired()
        return self._data_map.size()

    def keys(self) -> List[str]:
        """KEYS. 전체 유효 키 목록(순서 미보장)."""
        self._purge_expired()
        return self._data_map.keys()

    # ═══════════════════════════════════════════════════════
    # 메모리 관리 명령 (2개)
    # ═══════════════════════════════════════════════════════

    def config_set_maxmemory(self, bytes_val: int) -> bool:
        """CONFIG SET maxmemory <bytes>. 성공 시 True."""
        self._maxmemory = bytes_val
        return True

    def info_memory(self) -> Tuple[int, int, int]:
        """INFO memory. (used_memory, maxmemory, evicted_keys) 반환."""
        self._purge_expired()
        return (self._used_memory, self._maxmemory, self._evicted_keys)

    # ═══════════════════════════════════════════════════════
    # TTL 명령 (2개)
    # ═══════════════════════════════════════════════════════

    def expire(self, key: str, seconds: int) -> int:
        """EXPIRE key seconds. 설정 성공 1, 키 없으면 0."""
        self._purge_expired()

        if not self._data_map.contains(key):
            return 0

        if seconds <= 0:
            # 즉시 만료 = 삭제
            self._delete_key(key)
            return 1

        expire_at = self._clock() + seconds
        self._expiry_map.put(key, expire_at)
        self._expiry_heap.push((expire_at, key))
        return 1

    def ttl(self, key: str) -> int:
        """TTL key. 남은 초, -1(TTL 없음), -2(키 없음)."""
        self._purge_expired()

        if not self._data_map.contains(key):
            return -2

        current_expire: Optional[float] = self._expiry_map.get(key)
        if current_expire is None:
            return -1

        now = self._clock()
        if now >= current_expire:
            # 이미 만료 → 삭제
            self._delete_key(key)
            return -2

        return math.ceil(current_expire - now)
