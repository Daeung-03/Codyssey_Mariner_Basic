import unittest

from mini_redis.min_heap import MinHeap


class MinHeapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.heap = MinHeap()

    def test_push_and_pop_returns_ascending_order(self) -> None:
        items = [(5, "e"), (1, "a"), (3, "c"), (2, "b"), (4, "d")]
        for item in items:
            self.heap.push(item)

        results = [self.heap.pop() for _ in range(5)]
        expire_times = [r[0] for r in results]

        self.assertEqual(expire_times, [1, 2, 3, 4, 5])

    def test_peek_returns_minimum_without_removal(self) -> None:
        self.heap.push((10, "x"))
        self.heap.push((3, "y"))
        self.heap.push((7, "z"))

        self.assertEqual(self.heap.peek(), (3, "y"))
        self.assertEqual(self.heap.size(), 3)

    def test_size_tracks_insertions_and_removals(self) -> None:
        self.assertEqual(self.heap.size(), 0)

        self.heap.push((1, "a"))
        self.heap.push((2, "b"))
        self.assertEqual(self.heap.size(), 2)

        self.heap.pop()
        self.assertEqual(self.heap.size(), 1)

    def test_pop_and_peek_raise_on_empty_heap(self) -> None:
        with self.assertRaises(IndexError):
            self.heap.pop()
        with self.assertRaises(IndexError):
            self.heap.peek()

    def test_duplicate_priorities_are_handled(self) -> None:
        self.heap.push((5, "first"))
        self.heap.push((5, "second"))
        self.heap.push((5, "third"))

        results = [self.heap.pop() for _ in range(3)]
        # 모두 꺼낼 수 있고 우선순위는 전부 5
        self.assertTrue(all(r[0] == 5 for r in results))
        self.assertEqual(self.heap.size(), 0)

    def test_single_element(self) -> None:
        self.heap.push((42, "only"))

        self.assertEqual(self.heap.peek(), (42, "only"))
        self.assertEqual(self.heap.pop(), (42, "only"))
        self.assertEqual(self.heap.size(), 0)


if __name__ == "__main__":
    unittest.main()
