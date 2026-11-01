import json
import unittest
from pathlib import Path

ORDERS = json.loads((Path(__file__).resolve().parents[1] / "data/orders.json").read_text(encoding="utf-8"))["orders"]

class DemoOrderDataTests(unittest.TestCase):
    def test_has_twenty_unique_demo_orders(self):
        self.assertEqual(len(ORDERS), 20)
        ids = [row["order_id"] for row in ORDERS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(row.get("is_demo") is True for row in ORDERS))

    def test_covers_expected_lifecycle_statuses(self):
        statuses = {row["status"] for row in ORDERS}
        self.assertTrue({"待付款", "处理中", "已发货", "已完成", "退款中", "已退款", "已取消"}.issubset(statuses))

    def test_refund_timestamps_are_consistent(self):
        for row in ORDERS:
            if row["status"] == "退款中":
                self.assertIsNotNone(row["refund_started_date"])
                self.assertIsNone(row["refund_completed_date"])
            if row["status"] == "已退款":
                self.assertIsNotNone(row["refund_started_date"])
                self.assertIsNotNone(row["refund_completed_date"])

if __name__ == "__main__":
    unittest.main()
