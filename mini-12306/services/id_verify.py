import re


def verify_identity(real_name, id_card, phone):
    """模拟第三方实名认证服务。"""
    if not real_name or len(real_name) < 2:
        return False, "姓名格式不正确"
    if not re.match(r"^\d{17}[\dXx]$", id_card):
        return False, "身份证号格式不正确"
    if not re.match(r"^1\d{10}$", phone):
        return False, "手机号格式不正确"
    return True, "实名认证通过"
