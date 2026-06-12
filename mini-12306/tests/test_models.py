"""实体类单元测试。"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from models import Order, User
from tests.base import FlaskTestCase
from utils import generate_order_no


class TestUserModel(FlaskTestCase):
    def test_set_and_check_password(self):
        user = User(
            username="alice",
            real_name="爱丽丝",
            id_card="110101199001011234",
            phone="13800138001",
        )
        user.set_password("secret123")
        self.assertTrue(user.check_password("secret123"))
        self.assertFalse(user.check_password("wrong"))

    def test_password_hash_not_plaintext(self):
        user = User(
            username="bob",
            real_name="鲍勃",
            id_card="110101199001011235",
            phone="13800138002",
        )
        user.set_password("secret123")
        self.assertNotEqual(user.password_hash, "secret123")


class TestOrderModel(FlaskTestCase):
    def test_order_default_status(self):
        user = User(
            username="carol",
            real_name="卡罗",
            id_card="110101199001011236",
            phone="13800138003",
        )
        user.set_password("secret123")
        db.session.add(user)
        db.session.flush()

        order = Order(
            order_no=generate_order_no(),
            user_id=user.id,
            total_amount=553.0,
        )
        db.session.add(order)
        db.session.commit()

        self.assertEqual(order.status, "待支付")
        self.assertIsNone(order.paid_at)


if __name__ == "__main__":
    unittest.main()
