from datetime import datetime, timedelta

from flask import Blueprint, flash, render_template, request

from models import Station, Train, TrainSchedule, SeatInventory
from timezone import today as get_today

train_bp = Blueprint("train", __name__)

SEAT_TYPE_ORDER = ["二等座", "一等座", "硬卧", "软卧"]

def _parse_search_params():
    if request.method == "POST":
        return (
            request.form.get("from_station", "").strip(),
            request.form.get("to_station", "").strip(),
            request.form.get("travel_date", "").strip(),
        )
    return (
        request.args.get("from_station", "").strip(),
        request.args.get("to_station", "").strip(),
        request.args.get("travel_date", "").strip(),
    )


def _search_trains(from_station, to_station, travel_date, today, max_query_date):
    if not all([from_station, to_station, travel_date]):
        return None, "请填写完整的查询条件", "warning"

    if from_station == to_station:
        return None, "出发地和目的地不能相同", "warning"

    try:
        date_obj = datetime.strptime(travel_date, "%Y-%m-%d").date()
    except ValueError:
        return None, "日期格式不正确", "danger"

    if date_obj < today or date_obj > max_query_date:
        date_range_message = (
            f"仅支持查询最近14天（{today.strftime('%Y-%m-%d')} 至 "
            f"{max_query_date.strftime('%Y-%m-%d')}）的车次"
        )
        return None, date_range_message, "warning"

    from_st = Station.query.filter_by(name=from_station).first()
    to_st = Station.query.filter_by(name=to_station).first()
    if not from_st or not to_st:
        return None, "车站不存在", "danger"

    schedules = (
        TrainSchedule.query.join(Train)
        .filter(
            TrainSchedule.travel_date == date_obj,
            TrainSchedule.status == "正常",
            Train.from_station_id == from_st.id,
            Train.to_station_id == to_st.id,
        )
        .order_by(Train.departure_time)
        .all()
    )

    results = []
    for sch in schedules:
        inv_map = {
            inv.seat_type: inv
            for inv in SeatInventory.query.filter_by(schedule_id=sch.id).all()
        }
        results.append({"schedule": sch, "inventories": inv_map})

    return results, None, None


@train_bp.route("/search", methods=["GET", "POST"])
def search():
    stations = Station.query.order_by(Station.city, Station.name).all()
    today = get_today()
    max_query_date = today + timedelta(days=13)
    min_query_date_str = today.strftime("%Y-%m-%d")
    max_query_date_str = max_query_date.strftime("%Y-%m-%d")
    date_range_message = (
        f"仅支持查询最近14天（{min_query_date_str} 至 {max_query_date_str}）的车次"
    )

    from_station, to_station, travel_date = _parse_search_params()
    if not travel_date:
        travel_date = min_query_date_str

    results = None
    has_searched = False

    if request.method == "POST" or request.args.get("from_station"):
        has_searched = True
        results, error_msg, error_category = _search_trains(
            from_station, to_station, travel_date, today, max_query_date
        )
        if error_msg:
            flash(error_msg, error_category)
            results = []

    quick_dates = [
        {"label": "今天", "value": today.strftime("%Y-%m-%d")},
        {"label": "明天", "value": (today + timedelta(days=1)).strftime("%Y-%m-%d")},
        {"label": "后天", "value": (today + timedelta(days=2)).strftime("%Y-%m-%d")},
    ]

    return render_template(
        "train/search.html",
        stations=stations,
        results=results,
        has_searched=has_searched,
        from_station=from_station,
        to_station=to_station,
        travel_date=travel_date,
        min_query_date=min_query_date_str,
        max_query_date=max_query_date_str,
        date_range_message=date_range_message,
        seat_types=SEAT_TYPE_ORDER,
        quick_dates=quick_dates,
    )


@train_bp.route("/detail/<int:schedule_id>")
def detail(schedule_id):
    schedule = TrainSchedule.query.get_or_404(schedule_id)
    inventories = SeatInventory.query.filter_by(schedule_id=schedule_id).all()
    return render_template(
        "train/detail.html", schedule=schedule, inventories=inventories
    )
