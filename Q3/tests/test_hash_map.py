import unittest

from mini_redis.hash_map import HashMap


class HashMapTest(unittest.TestCase):
    def test_put_get_update_and_contains(self) -> None:
        hash_map = HashMap()

        hash_map.put("name", "Alice")
        hash_map.put("nullable", None)

        self.assertEqual(hash_map.get("name"), "Alice")
        self.assertTrue(hash_map.contains("nullable"))
        self.assertIsNone(hash_map.get("nullable"))
        self.assertFalse(hash_map.contains("missing"))
        self.assertEqual(hash_map.size(), 2)

        hash_map.put("name", "Bob")

        self.assertEqual(hash_map.get("name"), "Bob")
        self.assertEqual(hash_map.size(), 2)

    def test_collision_uses_same_bucket_chain(self) -> None:
        hash_map = HashMap(initial_capacity=4)

        hash_map.put("a", 1)
        hash_map.put("e", 2)

        collision_bucket = hash_map._buckets[hash_map._hash("a")]
        self.assertIsNotNone(collision_bucket)
        self.assertEqual(collision_bucket.size, 2)
        self.assertEqual(hash_map.get("a"), 1)
        self.assertEqual(hash_map.get("e"), 2)

    def test_remove_preserves_other_colliding_entries(self) -> None:
        hash_map = HashMap(initial_capacity=4)
        hash_map.put("a", 1)
        hash_map.put("e", 2)
        index = hash_map._hash("a")

        self.assertTrue(hash_map.remove("a"))
        self.assertFalse(hash_map.contains("a"))
        self.assertEqual(hash_map.get("e"), 2)
        self.assertEqual(hash_map.size(), 1)
        self.assertIsNotNone(hash_map._buckets[index])

        self.assertTrue(hash_map.remove("e"))
        self.assertIsNone(hash_map._buckets[index])
        self.assertEqual(hash_map.size(), 0)
        self.assertFalse(hash_map.remove("missing"))

    def test_resize_occurs_only_above_point_seven_five(self) -> None:
        hash_map = HashMap(initial_capacity=4)

        for key in ("a", "b", "c"):
            hash_map.put(key, key.upper())

        self.assertEqual(hash_map._capacity, 4)

        hash_map.put("d", "D")

        self.assertEqual(hash_map._capacity, 8)
        self.assertEqual(hash_map.size(), 4)
        for key in ("a", "b", "c", "d"):
            self.assertEqual(hash_map.get(key), key.upper())

    def test_keys_returns_every_stored_key(self) -> None:
        hash_map = HashMap()
        for key in ("alpha", "beta", "한글"):
            hash_map.put(key, key)

        self.assertCountEqual(hash_map.keys(), ["alpha", "beta", "한글"])

        hash_map.remove("beta")
        self.assertCountEqual(hash_map.keys(), ["alpha", "한글"])

    def test_initial_capacity_must_be_positive(self) -> None:
        with self.assertRaises(ValueError):
            HashMap(initial_capacity=0)


if __name__ == "__main__":
    unittest.main()
