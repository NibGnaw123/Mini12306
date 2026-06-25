"""通知服务单元测试（Mock 短信依赖）。"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from models import Notification, User
from services.notify import create_notification
from tests.base import FlaskTestCase


class TestCreateNotification(FlaskTestCase):
    def setUp(self):
        super().setUp()
        self.user = User(
            username="testuser",
            real_name="测试用户",
            id_card="110101199001011234",
            phone="13800138000",
        )
        self.user.set_password("password123")
        db.session.add(self.user)
        db.session.commit()

    @patch("services.notify.send_sms")
    def test_create_notification_persists_record(self, mock_send_sms):
        notification = create_notification(
            db.session,
            self.user,
            "支付成功",
            "订单 ORD202606120001 支付成功",
        )
        db.session.commit()

        self.assertIsInstance(notification, Notification)
        self.assertEqual(notification.user_id, self.user.id)
        self.assertEqual(notification.title, "支付成功")
        self.assertFalse(notification.is_read)

        saved = Notification.query.filter_by(user_id=self.user.id).first()
        self.assertIsNotNone(saved)
        self.assertIn("ORD202606120001", saved.content)

    @patch("services.notify.send_sms")
    def test_create_notification_triggers_sms(self, mock_send_sms):
        create_notification(db.session, self.user, "退票成功", "退款已完成")
        mock_send_sms.assert_called_once_with(
            "13800138000",
            "退票成功: 退款已完成",
        )


if __name__ == "__main__":
    unittest.main()
