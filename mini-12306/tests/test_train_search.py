"""车次查询核心逻辑单元测试。"""

import os
import sys
import unittest
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from routes.train import _search_trains
from tests.base import FlaskTestCase


class TestSearchTrains(FlaskTestCase):
    max_query_date = None

    def setUp(self):
        super().setUp()
        self.max_query_date = self.travel_date + timedelta(days=Config.SCHEDULE_DAYS - 1)

    def test_missing_params(self):
        results, msg, category = _search_trains("", "上海虹桥", "", self.travel_date, self.travel_date)
        self.assertIsNone(results)
        self.assertEqual(msg, "请填写完整的查询条件")
        self.assertEqual(category, "warning")

    def test_same_station(self):
        results, msg, category = _search_trains(
            "北京南",
            "北京南",
            self.travel_date.strftime("%Y-%m-%d"),
            self.travel_date,
            self.max_query_date,
        )
        self.assertIsNone(results)
        self.assertEqual(msg, "出发地和目的地不能相同")

    def test_invalid_date_format(self):
        results, msg, category = _search_trains(
            "北京南",
            "上海虹桥",
            "2026/06/12",
            self.travel_date,
            self.max_query_date,
        )
        self.assertIsNone(results)
        self.assertEqual(msg, "日期格式不正确")
        self.assertEqual(category, "danger")

    def test_date_out_of_range_past(self):
        past_date = self.travel_date - timedelta(days=1)
        results, msg, category = _search_trains(
            "北京南",
            "上海虹桥",
            past_date.strftime("%Y-%m-%d"),
            self.travel_date,
            self.max_query_date,
        )
        self.assertIsNone(results)
        self.assertIn(f"仅支持查询最近{Config.SCHEDULE_DAYS}天", msg)

    def test_date_out_of_range_future(self):
        future_date = self.travel_date + timedelta(days=Config.SCHEDULE_DAYS)
        results, msg, category = _search_trains(
            "北京南",
            "上海虹桥",
            future_date.strftime("%Y-%m-%d"),
            self.travel_date,
            self.max_query_date,
        )
        self.assertIsNone(results)
        self.assertIn(f"仅支持查询最近{Config.SCHEDULE_DAYS}天", msg)

    def test_station_not_found(self):
        results, msg, category = _search_trains(
            "不存在站",
            "上海虹桥",
            self.travel_date.strftime("%Y-%m-%d"),
            self.travel_date,
            self.max_query_date,
        )
        self.assertIsNone(results)
        self.assertEqual(msg, "车站不存在")

    def test_valid_search_returns_schedule(self):
        results, msg, category = _search_trains(
            "北京南",
            "上海虹桥",
            self.travel_date.strftime("%Y-%m-%d"),
            self.travel_date,
            self.max_query_date,
        )
        self.assertIsNone(msg)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["schedule"].id, self.schedule.id)
        self.assertIn("二等座", results[0]["inventories"])
        self.assertEqual(results[0]["inventories"]["二等座"].remaining, 50)


if __name__ == "__main__":
    unittest.main()
