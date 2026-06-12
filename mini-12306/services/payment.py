import uuid
from datetime import datetime


def create_payment(amount):
    """模拟创建支付订单。"""
    return {
        "payment_no": f"PAY{uuid.uuid4().hex[:16].upper()}",
        "amount": amount,
        "status": "待支付",
    }


def process_payment(payment_no, amount):
    """模拟在线支付，始终成功。"""
    return {
        "payment_no": payment_no,
        "amount": amount,
        "status": "支付成功",
        "paid_at": datetime.utcnow(),
    }


def process_refund(amount):
    """模拟退款处理。"""
    return {
        "refund_no": f"REF{uuid.uuid4().hex[:16].upper()}",
        "amount": amount,
        "status": "退款成功",
        "refunded_at": datetime.utcnow(),
    }
