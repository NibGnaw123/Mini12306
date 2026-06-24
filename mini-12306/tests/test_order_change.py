"""改签与已发车状态单元测试。"""

import os
import sys
import unittest
from datetime import time, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from extensions import db
from models import (
    ChangeRecord,
    Order,
    Passenger,
    SeatInventory,
    Ticket,
    Train,
    TrainSchedule,
    User,
)
from tests.base import FlaskTestCase
from timezone import now, today
from utils import (
    get_changeable_schedules,
    order_has_changed,
    sync_order_departed_status,
    ticket_is_change_result,
    validate_change_eligibility,
)


class TestOrderChangeRules(FlaskTestCase):
    def _create_paid_order(self, schedule=None, departure_time=None):
        if schedule is None:
            schedule = self.schedule
        if departure_time:
            self.train.departure_time = departure_time
            db.session.commit()

        user = User(
            username="tester",
            real_name="测试用户",
            id_card="110101199001011235",
            phone="13800000001",
        )
        user.set_password("test123")
        db.session.add(user)
        db.session.flush()

        passenger = Passenger(
            user_id=user.id,
            name="测试用户",
            id_card="110101199001011235",
            phone="13800000001",
        )
        db.session.add(passenger)
        db.session.flush()

        order = Order(
            order_no="ORDTEST001",
            user_id=user.id,
            status="已出票",
            total_amount=553.0,
            paid_at=now(),
        )
        db.session.add(order)
        db.session.flush()

        ticket = Ticket(
            order_id=order.id,
            schedule_id=schedule.id,
            passenger_id=passenger.id,
            seat_type="二等座",
            seat_no="201-01",
            price=553.0,
            status="已出票",
        )
        db.session.add(ticket)
        db.session.commit()
        return user, order, ticket

    def _add_same_day_train(self, train_no, departure_time):
        train = Train(
            train_no=train_no,
            name="京沪高铁",
            from_station_id=self.beijing.id,
            to_station_id=self.shanghai.id,
            departure_time=departure_time,
            arrival_time=time(14, 0),
            duration_minutes=300,
            distance_km=1318,
        )
        db.session.add(train)
        db.session.flush()
        schedule = TrainSchedule(
            train_id=train.id,
            travel_date=self.travel_date,
            status="正常",
        )
        db.session.add(schedule)
        db.session.flush()
        db.session.add(
            SeatInventory(
                schedule_id=schedule.id,
                seat_type="二等座",
                total=100,
                remaining=10,
                price=553.0,
            )
        )
        db.session.commit()
        return schedule

    def test_sync_order_departed_status(self):
        _, order, _ = self._create_paid_order(departure_time=time(8, 0))
        fake_now = now().replace(hour=9, minute=0, second=0, microsecond=0)
        with patch("utils.now", return_value=fake_now):
            self.assertTrue(sync_order_departed_status(order))
        self.assertEqual(order.status, "已发车")

    def test_order_has_changed(self):
        _, order, ticket = self._create_paid_order()
        self.assertFalse(order_has_changed(order))

        other_order = Order(
            order_no="ORDTEST002",
            user_id=order.user_id,
            status="已出票",
            total_amount=553.0,
            paid_at=now(),
        )
        db.session.add(other_order)
        db.session.flush()
        new_ticket = Ticket(
            order_id=other_order.id,
            schedule_id=self.schedule.id,
            passenger_id=ticket.passenger_id,
            seat_type="二等座",
            seat_no="201-02",
            price=553.0,
            status="已出票",
        )
        db.session.add(new_ticket)
        db.session.flush()
        db.session.add(
            ChangeRecord(
                old_ticket_id=ticket.id,
                new_ticket_id=new_ticket.id,
                price_diff=0,
            )
        )
        db.session.commit()
        self.assertTrue(order_has_changed(order))

    def test_validate_change_blocks_repeat_change(self):
        _, order, ticket = self._create_paid_order()
        db.session.add(
            ChangeRecord(
                old_ticket_id=ticket.id,
                new_ticket_id=ticket.id,
                price_diff=0,
            )
        )
        db.session.commit()

        ok, msg, _ = validate_change_eligibility(ticket, Config.CHANGE_DEADLINE_HOURS)
        self.assertFalse(ok)
        self.assertIn("已改签过", msg)

    def test_validate_change_blocks_within_two_hours(self):
        _, _, ticket = self._create_paid_order(departure_time=time(12, 0))
        fake_now = now().replace(hour=11, minute=0, second=0, microsecond=0)
        with patch("utils.now", return_value=fake_now):
            ok, msg, departed = validate_change_eligibility(
                ticket, Config.CHANGE_DEADLINE_HOURS
            )
        self.assertFalse(ok)
        self.assertIn("发车前2小时内不可改签", msg)
        self.assertFalse(departed)

    def test_validate_change_allows_after_departure(self):
        _, order, ticket = self._create_paid_order(departure_time=time(8, 0))
        fake_now = now().replace(hour=9, minute=0, second=0, microsecond=0)
        with patch("utils.now", return_value=fake_now):
            sync_order_departed_status(order)
            ok, msg, departed = validate_change_eligibility(
                ticket, Config.CHANGE_DEADLINE_HOURS
            )
        self.assertTrue(ok)
        self.assertIsNone(msg)
        self.assertTrue(departed)

    def test_get_changeable_schedules_not_departed_future_over_two_hours(self):
        _, _, ticket = self._create_paid_order(departure_time=time(9, 0))
        tomorrow = self.travel_date + timedelta(days=1)
        future_schedule = TrainSchedule(
            train_id=self.train.id,
            travel_date=tomorrow,
            status="正常",
        )
        db.session.add(future_schedule)
        db.session.flush()
        db.session.add(
            SeatInventory(
                schedule_id=future_schedule.id,
                seat_type="二等座",
                total=100,
                remaining=10,
                price=553.0,
            )
        )
        within_two_hours = self._add_same_day_train("G9", time(11, 30))
        db.session.commit()

        fake_now = now().replace(hour=10, minute=0, second=0, microsecond=0)
        with patch("utils.now", return_value=fake_now):
            schedules = get_changeable_schedules(
                ticket, departed=False, change_deadline_hours=Config.CHANGE_DEADLINE_HOURS
            )

        schedule_ids = {s.id for s in schedules}
        self.assertIn(future_schedule.id, schedule_ids)
        self.assertNotIn(within_two_hours.id, schedule_ids)

    def test_validate_change_blocks_change_result_ticket(self):
        _, order, ticket = self._create_paid_order()
        new_order = Order(
            order_no="ORDTEST003",
            user_id=order.user_id,
            status="已改签",
            total_amount=553.0,
            paid_at=now(),
        )
        db.session.add(new_order)
        db.session.flush()
        new_ticket = Ticket(
            order_id=new_order.id,
            schedule_id=self.schedule.id,
            passenger_id=ticket.passenger_id,
            seat_type="二等座",
            seat_no="201-03",
            price=553.0,
            status="已出票",
        )
        db.session.add(new_ticket)
        db.session.flush()
        db.session.add(
            ChangeRecord(
                old_ticket_id=ticket.id,
                new_ticket_id=new_ticket.id,
                price_diff=0,
            )
        )
        db.session.commit()

        ok, msg, _ = validate_change_eligibility(
            new_ticket, Config.CHANGE_DEADLINE_HOURS
        )
        self.assertFalse(ok)
        self.assertIn("不可", msg)

    def test_get_changeable_schedules_after_departure_same_day_only(self):
        _, _, ticket = self._create_paid_order(departure_time=time(8, 0))
        later_today = self._add_same_day_train("G3", time(14, 0))
        future_day = TrainSchedule(
            train_id=self.train.id,
            travel_date=self.travel_date + timedelta(days=1),
            status="正常",
        )
        db.session.add(future_day)
        db.session.commit()

        fake_now = now().replace(hour=9, minute=0, second=0, microsecond=0)
        with patch("utils.now", return_value=fake_now):
            schedules = get_changeable_schedules(
                ticket, departed=True, change_deadline_hours=Config.CHANGE_DEADLINE_HOURS
            )

        schedule_ids = {s.id for s in schedules}
        self.assertIn(later_today.id, schedule_ids)
        self.assertNotIn(future_day.id, schedule_ids)


if __name__ == "__main__":
    unittest.main()
