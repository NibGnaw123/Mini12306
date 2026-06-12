"""实名认证服务单元测试。"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.id_verify import verify_identity


class TestVerifyIdentity(unittest.TestCase):
    def test_valid_identity(self):
        ok, msg = verify_identity("张三", "110101199001011234", "13800138000")
        self.assertTrue(ok, msg="合法身份信息应通过认证")
        self.assertEqual(msg, "实名认证通过")

    def test_empty_name(self):
        ok, msg = verify_identity("", "110101199001011234", "13800138000")
        self.assertFalse(ok)
        self.assertEqual(msg, "姓名格式不正确")

    def test_name_too_short(self):
        ok, msg = verify_identity("张", "110101199001011234", "13800138000")
        self.assertFalse(ok)
        self.assertEqual(msg, "姓名格式不正确")

    def test_name_boundary_two_chars(self):
        ok, msg = verify_identity("李四", "110101199001011234", "13800138000")
        self.assertTrue(ok, msg="两位姓名处于合法边界")

    def test_invalid_id_card_length(self):
        ok, msg = verify_identity("王五", "123456", "13800138000")
        self.assertFalse(ok)
        self.assertEqual(msg, "身份证号格式不正确")

    def test_invalid_id_card_checksum(self):
        ok, msg = verify_identity("王五", "11010119900101123A", "13800138000")
        self.assertFalse(ok)
        self.assertEqual(msg, "身份证号格式不正确")

    def test_id_card_with_lowercase_x(self):
        ok, msg = verify_identity("王五", "11010119900101123x", "13800138000")
        self.assertTrue(ok, msg="身份证号末位小写 x 应被接受")

    def test_invalid_phone_not_start_with_one(self):
        ok, msg = verify_identity("王五", "110101199001011234", "23800138000")
        self.assertFalse(ok)
        self.assertEqual(msg, "手机号格式不正确")

    def test_invalid_phone_length(self):
        ok, msg = verify_identity("王五", "110101199001011234", "1380013800")
        self.assertFalse(ok)
        self.assertEqual(msg, "手机号格式不正确")


if __name__ == "__main__":
    unittest.main()
