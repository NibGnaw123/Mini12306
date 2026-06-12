import uuid
from datetime import datetime, date, time
from functools import wraps

from flask import flash, redirect, session, url_for, request

from extensions import db
from models import AuditLog
from timezone import now


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("请先登录", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("is_admin"):
            flash("需要管理员权限", "danger")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated


def generate_order_no():
    return f"ORD{now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"


def generate_seat_no(seat_type, index):
    car = (index // 20) + 1
    seat = (index % 20) + 1
    prefix = {"二等座": "2", "一等座": "1", "硬卧": "H", "软卧": "S"}.get(seat_type, "X")
    return f"{prefix}{car:02d}-{seat:02d}"


def log_action(user_id, action, detail=""):
    log = AuditLog(
        user_id=user_id,
        action=action,
        detail=detail,
        ip=request.remote_addr,
    )
    db.session.add(log)


def combine_datetime(travel_date, travel_time):
    return datetime.combine(travel_date, travel_time)


ORDER_STATUS_LABELS = {
    "待支付": "warning",
    "已支付": "info",
    "已出票": "success",
    "已退票": "secondary",
    "已改签": "primary",
}
