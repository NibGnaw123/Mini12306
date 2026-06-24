import uuid
from datetime import datetime, date, time, timedelta
from functools import wraps

from flask import flash, redirect, session, url_for, request

from extensions import db
from models import AuditLog, ChangeRecord, Train, TrainSchedule
from timezone import now, today


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


def get_ticket_departure(ticket):
    schedule = ticket.schedule
    return combine_datetime(schedule.travel_date, schedule.train.departure_time)


def ticket_has_departed(ticket):
    return now() > get_ticket_departure(ticket)


def sync_order_departed_status(order):
    if order.status != "已出票":
        return False
    for ticket in order.tickets:
        if ticket.status != "已出票":
            continue
        if ticket_has_departed(ticket):
            order.status = "已发车"
            return True
    return False


def sync_orders_departed_status(orders):
    changed = False
    for order in orders:
        if sync_order_departed_status(order):
            changed = True
    return changed


def order_has_changed(order):
    ticket_ids = [t.id for t in order.tickets]
    if not ticket_ids:
        return False
    return (
        ChangeRecord.query.filter(ChangeRecord.old_ticket_id.in_(ticket_ids)).first()
        is not None
    )


def ticket_is_change_result(ticket):
    return ChangeRecord.query.filter_by(new_ticket_id=ticket.id).first() is not None


def validate_change_eligibility(ticket, change_deadline_hours):
    order = ticket.order
    if ticket.status != "已出票":
        return False, "该车票不可改签", False
    if order.status not in ("已出票", "已发车"):
        return False, "该订单不可改签", False
    if order_has_changed(order) or ticket_is_change_result(ticket):
        return False, "该订单已改签过，不可再次改签", False

    departed = ticket_has_departed(ticket)
    depart_dt = get_ticket_departure(ticket)
    if not departed and now() > depart_dt - timedelta(hours=change_deadline_hours):
        return False, "发车前2小时内不可改签", False

    return True, None, departed


def get_changeable_schedules(ticket, departed, change_deadline_hours=2):
    schedule = ticket.schedule
    train = schedule.train
    query = (
        TrainSchedule.query.join(Train)
        .filter(
            TrainSchedule.status == "正常",
            Train.from_station_id == train.from_station_id,
            Train.to_station_id == train.to_station_id,
            TrainSchedule.id != schedule.id,
        )
    )
    if departed:
        query = query.filter(TrainSchedule.travel_date == schedule.travel_date)
        if schedule.travel_date == today():
            query = query.filter(Train.departure_time > now().time())
        candidates = query.all()
    else:
        candidates = query.all()
        deadline = now() + timedelta(hours=change_deadline_hours)
        candidates = [
            sch
            for sch in candidates
            if combine_datetime(sch.travel_date, sch.train.departure_time) > deadline
        ]
    return sorted(
        candidates,
        key=lambda sch: (sch.travel_date, sch.train.departure_time),
    )


ORDER_STATUS_LABELS = {
    "待支付": "warning",
    "已支付": "info",
    "已出票": "success",
    "已发车": "dark",
    "已退票": "secondary",
    "已改签": "primary",
}
