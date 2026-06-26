import unittest

from budget_app.models import Budget, Category, Transaction


class TestTransaction(unittest.TestCase):
    def test_round_trip(self):
        t = Transaction(
            id="TX-000001", type="expense", date="2024-01-15",
            amount=15000, category="food", memo="점심", tags=["meal"],
        )
        data = t.to_dict()
        self.assertEqual(data["id"], "TX-000001")
        restored = Transaction.from_dict(data)
        self.assertEqual(restored, t)

    def test_from_dict_defaults_memo_and_tags(self):
        data = {"id": "TX-000002", "type": "income", "date": "2024-01-01", "amount": 1000, "category": "salary"}
        restored = Transaction.from_dict(data)
        self.assertIsNone(restored.memo)
        self.assertEqual(restored.tags, [])


class TestCategory(unittest.TestCase):
    def test_round_trip(self):
        c = Category(name="food")
        self.assertEqual(Category.from_dict(c.to_dict()), c)


class TestBudget(unittest.TestCase):
    def test_round_trip(self):
        b = Budget(month="2024-01", amount=500000)
        self.assertEqual(Budget.from_dict(b.to_dict()), b)


if __name__ == "__main__":
    unittest.main()
