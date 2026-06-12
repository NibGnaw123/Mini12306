"""测试公共基类：提供内存数据库 Flask 应用上下文。"""

import os
import sys
import unittest
from datetime import date, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask

from config import Config
from extensions import db
from models import SeatInventory, Station, Train, TrainSchedule
from timezone import today


def create_test_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
    )
    db.init_app(app)
    return app


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_test_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.seed_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def seed_data(self):
        beijing = Station(name="北京南", city="北京", code="BJN")
        shanghai = Station(name="上海虹桥", city="上海", code="SHH")
        db.session.add_all([beijing, shanghai])
        db.session.flush()

        train = Train(
            train_no="G1",
            name="京沪高铁",
            from_station_id=beijing.id,
            to_station_id=shanghai.id,
            departure_time=time(9, 0),
            arrival_time=time(14, 0),
            duration_minutes=300,
            distance_km=1318,
        )
        db.session.add(train)
        db.session.flush()

        travel_date = today()
        schedule = TrainSchedule(
            train_id=train.id,
            travel_date=travel_date,
            status="正常",
        )
        db.session.add(schedule)
        db.session.flush()

        inventory = SeatInventory(
            schedule_id=schedule.id,
            seat_type="二等座",
            total=100,
            remaining=50,
            price=553.0,
        )
        db.session.add(inventory)
        db.session.commit()

        self.beijing = beijing
        self.shanghai = shanghai
        self.train = train
        self.schedule = schedule
        self.inventory = inventory
        self.travel_date = travel_date
