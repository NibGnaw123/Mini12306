from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import and_

from models import Station, Train, TrainSchedule, SeatInventory
from utils import login_required

train_bp = Blueprint("train", __name__)


@train_bp.route("/search", methods=["GET", "POST"])
def search():
    stations = Station.query.order_by(Station.city, Station.name).all()
    results = []
    from_station = to_station = travel_date = ""

    if request.method == "POST":
        from_station = request.form.get("from_station", "").strip()
        to_station = request.form.get("to_station", "").strip()
        travel_date = request.form.get("travel_date", "").strip()

        if not all([from_station, to_station, travel_date]):
            flash("请填写完整的查询条件", "warning")
        elif from_station == to_station:
            flash("出发地和目的地不能相同", "warning")
        else:
            try:
                date_obj = datetime.strptime(travel_date, "%Y-%m-%d").date()
            except ValueError:
                flash("日期格式不正确", "danger")
            else:
                from_st = Station.query.filter_by(name=from_station).first()
                to_st = Station.query.filter_by(name=to_station).first()
                if not from_st or not to_st:
                    flash("车站不存在", "danger")
                else:
                    schedules = (
                        TrainSchedule.query.join(Train)
                        .filter(
                            TrainSchedule.travel_date == date_obj,
                            TrainSchedule.status == "正常",
                            Train.from_station_id == from_st.id,
                            Train.to_station_id == to_st.id,
                        )
                        .all()
                    )
                    for sch in schedules:
                        invs = SeatInventory.query.filter_by(schedule_id=sch.id).all()
                        results.append({"schedule": sch, "inventories": invs})

    return render_template(
        "train/search.html",
        stations=stations,
        results=results,
        from_station=from_station,
        to_station=to_station,
        travel_date=travel_date,
    )


@train_bp.route("/detail/<int:schedule_id>")
def detail(schedule_id):
    schedule = TrainSchedule.query.get_or_404(schedule_id)
    inventories = SeatInventory.query.filter_by(schedule_id=schedule_id).all()
    return render_template(
        "train/detail.html", schedule=schedule, inventories=inventories
    )
