import unittest

from mini_redis.doubly_linked_list import DoublyLinkedList


class DoublyLinkedListTest(unittest.TestCase):
    def setUp(self) -> None:
        self.linked_list = DoublyLinkedList()

    def values(self):
        values = []
        current = self.linked_list.head.next
        while current is not self.linked_list.tail:
            values.append(current.data)
            current = current.next
        return values

    def test_empty_list_has_connected_sentinels(self) -> None:
        self.assertIs(self.linked_list.head.next, self.linked_list.tail)
        self.assertIs(self.linked_list.tail.prev, self.linked_list.head)
        self.assertIsNone(self.linked_list.head.prev)
        self.assertIsNone(self.linked_list.tail.next)
        self.assertEqual(self.linked_list.size, 0)

    def test_insert_front_and_back(self) -> None:
        front = self.linked_list.insert_front("middle")
        new_front = self.linked_list.insert_front("front")
        back = self.linked_list.insert_back("back")

        self.assertEqual(self.values(), ["front", "middle", "back"])
        self.assertEqual(self.linked_list.size, 3)
        self.assertIs(self.linked_list.head.next, new_front)
        self.assertIs(self.linked_list.tail.prev, back)
        self.assertIs(new_front.next, front)

    def test_remove_front_back_and_node(self) -> None:
        front = self.linked_list.insert_back("front")
        middle = self.linked_list.insert_back("middle")
        back = self.linked_list.insert_back("back")

        self.assertIs(self.linked_list.remove_front(), front)
        self.assertIs(self.linked_list.remove_back(), back)
        self.assertIs(self.linked_list.remove_node(middle), middle)

        self.assertEqual(self.values(), [])
        self.assertEqual(self.linked_list.size, 0)
        self.assertIsNone(front.prev)
        self.assertIsNone(front.next)
        self.assertIsNone(middle.prev)
        self.assertIsNone(middle.next)
        self.assertIsNone(back.prev)
        self.assertIsNone(back.next)

    def test_move_to_front_keeps_size(self) -> None:
        front = self.linked_list.insert_back("front")
        middle = self.linked_list.insert_back("middle")
        back = self.linked_list.insert_back("back")

        returned = self.linked_list.move_to_front(back)

        self.assertIs(returned, back)
        self.assertEqual(self.values(), ["back", "front", "middle"])
        self.assertEqual(self.linked_list.size, 3)
        self.assertIs(self.linked_list.head.next, back)
        self.assertIs(self.linked_list.tail.prev, middle)
        self.assertIs(back.next, front)

    def test_empty_removals_raise_index_error(self) -> None:
        with self.assertRaises(IndexError):
            self.linked_list.remove_front()
        with self.assertRaises(IndexError):
            self.linked_list.remove_back()

    def test_sentinel_or_detached_node_cannot_be_changed(self) -> None:
        node = self.linked_list.insert_front(None)
        self.linked_list.remove_node(node)

        with self.assertRaises(ValueError):
            self.linked_list.remove_node(self.linked_list.head)
        with self.assertRaises(ValueError):
            self.linked_list.move_to_front(self.linked_list.tail)
        with self.assertRaises(ValueError):
            self.linked_list.remove_node(node)
        with self.assertRaises(ValueError):
            self.linked_list.move_to_front(node)


if __name__ == "__main__":
    unittest.main()
