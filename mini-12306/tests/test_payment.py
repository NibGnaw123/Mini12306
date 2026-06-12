"""支付服务单元测试。"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.payment import create_payment, process_payment, process_refund


class TestCreatePayment(unittest.TestCase):
    def test_create_payment_structure(self):
        result = create_payment(553.0)
        self.assertEqual(result["amount"], 553.0)
        self.assertEqual(result["status"], "待支付")
        self.assertTrue(
            re.match(r"^PAY[0-9A-F]{16}$", result["payment_no"]),
            msg="支付单号格式不正确",
        )


class TestProcessPayment(unittest.TestCase):
    def test_process_payment_success(self):
        result = process_payment("PAY1234567890ABCDEF", 553.0)
        self.assertEqual(result["payment_no"], "PAY1234567890ABCDEF")
        self.assertEqual(result["amount"], 553.0)
        self.assertEqual(result["status"], "支付成功")
        self.assertIsNotNone(result["paid_at"])


class TestProcessRefund(unittest.TestCase):
    def test_process_refund_structure(self):
        result = process_refund(525.35)
        self.assertEqual(result["amount"], 525.35)
        self.assertEqual(result["status"], "退款成功")
        self.assertTrue(
            re.match(r"^REF[0-9A-F]{16}$", result["refund_no"]),
            msg="退款单号格式不正确",
        )
        self.assertIsNotNone(result["refunded_at"])


if __name__ == "__main__":
    unittest.main()
