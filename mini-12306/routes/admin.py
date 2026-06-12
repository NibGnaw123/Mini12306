from datetime import datetime, time, timedelta

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from extensions import db
from timezone import today
from models import (
    User,
    Station,
    Train,
    TrainSchedule,
    SeatInventory,
    Order,
    AuditLog,
)
from utils import admin_required, log_action

admin_bp = Blueprint("admin", __name__)

SEAT_TYPES = [
    ("二等座", 200, 553.5),
    ("一等座", 80, 933.5),
    ("硬卧", 120, 650.0),
    ("软卧", 40, 1050.0),
]


@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "users": User.query.filter_by(is_admin=False).count(),
        "trains": Train.query.count(),
        "orders": Order.query.count(),
        "today_orders": Order.query.filter(
            Order.created_at >= datetime.combine(today(), time.min)
        ).count(),
    }
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, logs=recent_logs)


@admin_bp.route("/users")
@admin_required
def users():
    user_list = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=user_list)


@admin_bp.route("/stations", methods=["GET", "POST"])
@admin_required
def stations():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        city = request.form.get("city", "").strip()
        code = request.form.get("code", "").strip().upper()
        if Station.query.filter((Station.name == name) | (Station.code == code)).first():
            flash("车站名称或代码已存在", "danger")
        else:
            station = Station(name=name, city=city, code=code)
            db.session.add(station)
            log_action(session["user_id"], "添加车站", name)
            db.session.commit()
            flash("车站添加成功", "success")
        return redirect(url_for("admin.stations"))

    station_list = Station.query.order_by(Station.city).all()
    return render_template("admin/stations.html", stations=station_list)


@admin_bp.route("/trains", methods=["GET", "POST"])
@admin_required
def trains():
    if request.method == "POST":
        train_no = request.form.get("train_no", "").strip()
        name = request.form.get("name", "").strip()
        from_id = request.form.get("from_station_id")
        to_id = request.form.get("to_station_id")
        dep = request.form.get("departure_time")
        arr = request.form.get("arrival_time")
        duration = request.form.get("duration_minutes")
        distance = request.form.get("distance_km")

        if Train.query.filter_by(train_no=train_no).first():
            flash("车次号已存在", "danger")
        else:
            train = Train(
                train_no=train_no,
                name=name,
                from_station_id=from_id,
                to_station_id=to_id,
                departure_time=datetime.strptime(dep, "%H:%M").time(),
                arrival_time=datetime.strptime(arr, "%H:%M").time(),
                duration_minutes=int(duration),
                distance_km=int(distance),
            )
            db.session.add(train)
            log_action(session["user_id"], "添加车次", train_no)
            db.session.commit()
            flash("车次添加成功", "success")
        return redirect(url_for("admin.trains"))

    train_list = Train.query.all()
    station_list = Station.query.all()
    return render_template(
        "admin/trains.html", trains=train_list, stations=station_list
    )


@admin_bp.route("/schedules", methods=["GET", "POST"])
@admin_required
def schedules():
    if request.method == "POST":
        train_id = request.form.get("train_id")
        travel_date = request.form.get("travel_date")
        date_obj = datetime.strptime(travel_date, "%Y-%m-%d").date()

        if TrainSchedule.query.filter_by(train_id=train_id, travel_date=date_obj).first():
            flash("该日期排班已存在", "danger")
        else:
            schedule = TrainSchedule(train_id=train_id, travel_date=date_obj)
            db.session.add(schedule)
            db.session.flush()
            for seat_type, total, price in SEAT_TYPES:
                inv = SeatInventory(
                    schedule_id=schedule.id,
                    seat_type=seat_type,
                    total=total,
                    remaining=total,
                    price=price,
                )
                db.session.add(inv)
            log_action(session["user_id"], "添加排班", f"车次{train_id} {travel_date}")
            db.session.commit()
            flash("排班添加成功", "success")
        return redirect(url_for("admin.schedules"))

    schedule_list = TrainSchedule.query.order_by(
        TrainSchedule.travel_date.desc()
    ).all()
    train_list = Train.query.all()
    return render_template(
        "admin/schedules.html", schedules=schedule_list, trains=train_list
    )


@admin_bp.route("/orders")
@admin_required
def orders():
    order_list = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=order_list)


@admin_bp.route("/logs")
@admin_required
def logs():
    log_list = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    return render_template("admin/logs.html", logs=log_list)
