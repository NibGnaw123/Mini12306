from datetime import timedelta

from flask import Blueprint, render_template

from config import Config
from models import Station
from timezone import today as get_today

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    today = get_today()
    return render_template(
        "index.html",
        stations=Station.query.order_by(Station.city, Station.name).all(),
        today=today.strftime("%Y-%m-%d"),
        min_date=today.strftime("%Y-%m-%d"),
        max_date=(today + timedelta(days=Config.SCHEDULE_DAYS - 1)).strftime("%Y-%m-%d"),
    )