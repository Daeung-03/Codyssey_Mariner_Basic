"""MiniRedis 통합 테스트.

가짜 시계를 주입하여 TTL을 결정적으로 검증하고,
LRU 퇴출, OOM, 기본 명령 결과를 확인한다.
"""

import unittest

from mini_redis.core import MiniRedis, OutOfMemoryError


class FakeClock:
    """테스트용 가짜 시계. advance()로 시간을 즉시 이동한다."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


class BasicCommandsTest(unittest.TestCase):
    """기본 명령의 대표 성공·실패 결과를 확인한다."""

    def setUp(self) -> None:
        self.clock = FakeClock()
        self.redis = MiniRedis(clock=self.clock)

    def test_set_get_del_exists(self) -> None:
        self.assertTrue(self.redis.set("name", "Alice"))
        self.assertEqual(self.redis.get("name"), "Alice")
        self.assertEqual(self.redis.exists("name"), 1)

        self.assertEqual(self.redis.delete("name"), 1)
        self.assertIsNone(self.redis.get("name"))
        self.assertEqual(self.redis.exists("name"), 0)
        self.assertEqual(self.redis.delete("name"), 0)

    def test_set_overwrites_value_and_clears_ttl(self) -> None:
        self.redis.set("k", "v1")
        self.redis.expire("k", 10)
        self.redis.set("k", "v2")

        self.assertEqual(self.redis.get("k"), "v2")
        self.assertEqual(self.redis.ttl("k"), -1)

    def test_dbsize_and_keys(self) -> None:
        self.assertEqual(self.redis.dbsize(), 0)
        self.assertEqual(self.redis.keys(), [])

        self.redis.set("a", "1")
        self.redis.set("b", "2")

        self.assertEqual(self.redis.dbsize(), 2)
        self.assertCountEqual(self.redis.keys(), ["a", "b"])

    def test_get_nonexistent_returns_none(self) -> None:
        self.assertIsNone(self.redis.get("missing"))


class LRUEvictionTest(unittest.TestCase):
    """작은 메모리 제한에서 접근 순서에 맞는 LRU 퇴출을 확인한다."""

    def setUp(self) -> None:
        self.clock = FakeClock()
        self.redis = MiniRedis(clock=self.clock)

    def test_lru_evicts_least_recently_used(self) -> None:
        # 각 엔트리: key(6 bytes "user:N") + value(다양)
        # user:1 = 6+5=11, user:2 = 6+3=9, user:3 = 6+7=13
        self.redis.config_set_maxmemory(30)

        self.redis.set("user:1", "Alice")  # used=11
        self.redis.set("user:2", "Bob")    # used=20
        self.redis.set("user:3", "Charlie")  # used=33 > 30 → LRU 퇴출

        # user:1이 가장 오래됨 → 퇴출
        self.assertIsNone(self.redis.get("user:1"))
        self.assertEqual(self.redis.get("user:2"), "Bob")
        self.assertEqual(self.redis.get("user:3"), "Charlie")

        used, maxmem, evicted = self.redis.info_memory()
        self.assertEqual(maxmem, 30)
        self.assertEqual(evicted, 1)
        self.assertLessEqual(used, 30)

    def test_get_refreshes_lru_order(self) -> None:
        self.redis.config_set_maxmemory(25)

        self.redis.set("a", "1234567")  # 1+7=8
        self.redis.set("b", "1234567")  # 1+7=8, used=16

        # GET a → a가 최근으로 이동
        self.redis.get("a")

        # 새 키 추가로 퇴출 유발 → b가 LRU
        self.redis.set("c", "1234567")  # used=24 → OK, 아직 25 이하
        self.redis.set("d", "1234567")  # used=32 > 25 → b 퇴출

        self.assertIsNone(self.redis.get("b"))
        self.assertEqual(self.redis.get("a"), "1234567")

    def test_config_set_maxmemory_does_not_evict_immediately(self) -> None:
        self.redis.set("big", "x" * 100)  # used=103
        self.redis.config_set_maxmemory(10)

        # 즉시 퇴출하지 않음
        self.assertEqual(self.redis.get("big"), "x" * 100)

        # 다음 SET에서 퇴출 발생
        self.redis.set("new", "y")
        # big은 퇴출됨
        self.assertIsNone(self.redis.get("big"))


class TTLTest(unittest.TestCase):
    """가짜 시계로 TTL 설정·만료와 lazy deletion을 확인한다."""

    def setUp(self) -> None:
        self.clock = FakeClock(start=100.0)
        self.redis = MiniRedis(clock=self.clock)

    def test_expire_and_ttl_basic(self) -> None:
        self.redis.set("k", "v")
        self.assertEqual(self.redis.expire("k", 10), 1)
        self.assertEqual(self.redis.ttl("k"), 10)

        self.clock.advance(7)
        self.assertEqual(self.redis.ttl("k"), 3)

        self.clock.advance(3)
        # 만료됨
        self.assertEqual(self.redis.ttl("k"), -2)
        self.assertIsNone(self.redis.get("k"))

    def test_expire_nonexistent_key(self) -> None:
        self.assertEqual(self.redis.expire("missing", 5), 0)

    def test_expire_zero_or_negative_deletes_immediately(self) -> None:
        self.redis.set("k", "v")
        self.assertEqual(self.redis.expire("k", 0), 1)
        self.assertIsNone(self.redis.get("k"))
        self.assertEqual(self.redis.exists("k"), 0)

        self.redis.set("k2", "v2")
        self.assertEqual(self.redis.expire("k2", -5), 1)
        self.assertIsNone(self.redis.get("k2"))

    def test_ttl_without_expiry_returns_minus_one(self) -> None:
        self.redis.set("k", "v")
        self.assertEqual(self.redis.ttl("k"), -1)

    def test_ttl_nonexistent_returns_minus_two(self) -> None:
        self.assertEqual(self.redis.ttl("ghost"), -2)

    def test_lazy_deletion_on_ttl_renewal(self) -> None:
        """TTL 갱신 후 이전 힙 항목이 무시되는지 확인한다."""
        self.redis.set("k", "v")
        self.redis.expire("k", 5)   # expire_at=105

        # TTL 갱신
        self.clock.advance(2)
        self.redis.expire("k", 10)  # expire_at=112

        # 원래 만료 시각(105) 지남 → 키는 여전히 존재해야 함
        self.clock.advance(5)  # now=107
        self.assertEqual(self.redis.get("k"), "v")
        self.assertEqual(self.redis.ttl("k"), 5)

        # 새 만료 시각(112) 지남
        self.clock.advance(5)  # now=112
        self.assertIsNone(self.redis.get("k"))

    def test_purge_expired_cleans_for_dbsize_and_keys(self) -> None:
        """접근하지 않은 만료 키도 DBSIZE/KEYS에서 제외된다."""
        self.redis.set("a", "1")
        self.redis.set("b", "2")
        self.redis.expire("a", 3)

        self.clock.advance(5)

        self.assertEqual(self.redis.dbsize(), 1)
        self.assertCountEqual(self.redis.keys(), ["b"])


class OOMTest(unittest.TestCase):
    """단일 엔트리 OOM과 UTF-8 바이트 계산을 확인한다."""

    def setUp(self) -> None:
        self.clock = FakeClock()
        self.redis = MiniRedis(clock=self.clock)

    def test_single_entry_exceeds_maxmemory_raises(self) -> None:
        self.redis.config_set_maxmemory(5)

        with self.assertRaises(OutOfMemoryError):
            self.redis.set("bigkey", "bigvalue")

        # 상태 변경 없음
        self.assertEqual(self.redis.dbsize(), 0)

    def test_overwrite_with_oom_preserves_existing(self) -> None:
        self.redis.config_set_maxmemory(10)
        self.redis.set("k", "ab")  # 1+2=3
        self.redis.expire("k", 99)

        with self.assertRaises(OutOfMemoryError):
            self.redis.set("k", "x" * 100)

        # 기존 값과 TTL 보존
        self.assertEqual(self.redis.get("k"), "ab")
        self.assertEqual(self.redis.ttl("k"), 99)

    def test_utf8_byte_calculation(self) -> None:
        self.redis.config_set_maxmemory(100)
        # "한글" = 6 bytes UTF-8, key "k" = 1 byte → total 7
        self.redis.set("k", "한글")

        used, _, _ = self.redis.info_memory()
        self.assertEqual(used, 7)


if __name__ == "__main__":
    unittest.main()
