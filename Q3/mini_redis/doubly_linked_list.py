"""이중 연결 리스트.

더미 head/tail 사이에 실제 데이터 노드를 저장하며,
삽입·삭제·이동을 모두 O(1)에 처리한다.
LRU 리스트와 해시맵 버킷 체인 양쪽에서 재사용된다.
"""

from typing import Any, Optional


class DoublyLinkedListNode:
    """이중 연결 리스트의 노드."""

    def __init__(self, data: Any = None) -> None:
        self.prev: Optional["DoublyLinkedListNode"] = None
        self.next: Optional["DoublyLinkedListNode"] = None
        self.data = data


class DoublyLinkedList:
    """더미 head와 tail 사이에 실제 데이터 노드를 저장한다."""

    def __init__(self) -> None:
        self.head = DoublyLinkedListNode()
        self.tail = DoublyLinkedListNode()
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0

    def _link_between(
        self,
        node: DoublyLinkedListNode,
        prev_node: DoublyLinkedListNode,
        next_node: DoublyLinkedListNode,
    ) -> None:
        """두 인접 노드 사이에 node를 연결한다."""
        prev_node.next = node
        node.prev = prev_node
        node.next = next_node
        next_node.prev = node

    def _unlink(self, node: DoublyLinkedListNode) -> None:
        """연결된 node를 분리하되 리스트 크기는 변경하지 않는다."""
        prev_node = node.prev
        next_node = node.next

        if prev_node is None or next_node is None:
            raise ValueError("node is not linked")

        prev_node.next = next_node
        next_node.prev = prev_node
        node.prev = None
        node.next = None

    def insert_front(self, data: Any) -> DoublyLinkedListNode:
        """리스트 앞에 데이터를 삽입하고 생성한 노드를 반환한다."""
        node = DoublyLinkedListNode(data)
        first_node = self.head.next
        if first_node is None:
            raise RuntimeError("list invariant is broken")

        self._link_between(node, self.head, first_node)
        self.size += 1
        return node

    def insert_back(self, data: Any) -> DoublyLinkedListNode:
        """리스트 뒤에 데이터를 삽입하고 생성한 노드를 반환한다."""
        node = DoublyLinkedListNode(data)
        last_node = self.tail.prev
        if last_node is None:
            raise RuntimeError("list invariant is broken")

        self._link_between(node, last_node, self.tail)
        self.size += 1
        return node

    def remove_front(self) -> DoublyLinkedListNode:
        """첫 실제 노드를 제거하며 빈 리스트에서는 IndexError를 발생시킨다."""
        if self.size == 0:
            raise IndexError("remove_front from empty list")

        first_node = self.head.next
        if first_node is None or first_node is self.tail:
            raise RuntimeError("list invariant is broken")

        return self.remove_node(first_node)

    def remove_back(self) -> DoublyLinkedListNode:
        """마지막 실제 노드를 제거하며 빈 리스트에서는 IndexError를 발생시킨다."""
        if self.size == 0:
            raise IndexError("remove_back from empty list")

        last_node = self.tail.prev
        if last_node is None or last_node is self.head:
            raise RuntimeError("list invariant is broken")

        return self.remove_node(last_node)

    def remove_node(
        self, node: DoublyLinkedListNode
    ) -> DoublyLinkedListNode:
        """전달받은 실제 노드를 O(1)에 제거하고 반환한다."""
        if node is self.head or node is self.tail:
            raise ValueError("cannot remove a sentinel node")

        self._unlink(node)
        self.size -= 1
        return node

    def move_to_front(
        self, node: DoublyLinkedListNode
    ) -> DoublyLinkedListNode:
        """전달받은 실제 노드를 리스트 앞으로 이동한다."""
        if node is self.head or node is self.tail:
            raise ValueError("cannot move a sentinel node")
        if node.prev is None or node.next is None:
            raise ValueError("node is not linked")
        if self.head.next is node:
            return node

        self._unlink(node)
        first_node = self.head.next
        if first_node is None:
            raise RuntimeError("list invariant is broken")
        self._link_between(node, self.head, first_node)
        return node
