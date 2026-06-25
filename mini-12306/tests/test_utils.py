"""utils 模块单元测试。"""

import os
import re
import sys
import unittest
from datetime import date, datetime, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import combine_datetime, generate_order_no, generate_seat_no


class TestGenerateOrderNo(unittest.TestCase):
    def test_order_no_format(self):
        order_no = generate_order_no()
        self.assertTrue(
            re.match(r"^ORD\d{14}[0-9A-F]{6}$", order_no),
            msg="订单号应以 ORD 开头，后接时间戳与 6 位随机码",
        )

    def test_order_no_unique(self):
        numbers = {generate_order_no() for _ in range(10)}
        self.assertEqual(len(numbers), 10, msg="连续生成的订单号应互不相同")


class TestGenerateSeatNo(unittest.TestCase):
    def test_second_class_seat_first_position(self):
        self.assertEqual(generate_seat_no("二等座", 0), "201-01")

    def test_second_class_seat_last_in_car(self):
        self.assertEqual(generate_seat_no("二等座", 19), "201-20")

    def test_second_class_seat_next_car(self):
        self.assertEqual(generate_seat_no("二等座", 20), "202-01")

    def test_first_class_seat_prefix(self):
        self.assertEqual(generate_seat_no("一等座", 0), "101-01")

    def test_hard_sleeper_prefix(self):
        self.assertEqual(generate_seat_no("硬卧", 0), "H01-01")

    def test_soft_sleeper_prefix(self):
        self.assertEqual(generate_seat_no("软卧", 0), "S01-01")

    def test_unknown_seat_type_uses_default_prefix(self):
        self.assertEqual(generate_seat_no("商务座", 0), "X01-01")


class TestCombineDatetime(unittest.TestCase):
    def test_combine_date_and_time(self):
        travel_date = date(2026, 6, 12)
        travel_time = time(9, 30, 0)
        result = combine_datetime(travel_date, travel_time)
        self.assertEqual(result, datetime(2026, 6, 12, 9, 30, 0))


if __name__ == "__main__":
    unittest.main()
