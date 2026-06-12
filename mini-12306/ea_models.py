"""EA class import stubs for the mini-12306 domain model.

This file is intentionally kept free of Flask-SQLAlchemy dynamic field
expressions so that Enterprise Architect can reliably reverse-engineer the
classes and associations from Python source code.

It is not used by the running Flask application. Runtime ORM definitions live
in models.py.
"""

from datetime import date, datetime, time
from typing import List, Optional


class User:
    id: int
    username: str
    password_hash: str
    real_name: str
    id_card: str
    phone: str
    is_admin: bool
    created_at: datetime

    passengers: List["Passenger"]
    orders: List["Order"]
    notifications: List["Notification"]


class Passenger:
    id: int
    user_id: int
    name: str
    id_card: str
    phone: str
    created_at: datetime

    user: User
    tickets: List["Ticket"]


class Station:
    id: int
    name: str
    city: str
    code: str


class Train:
    id: int
    train_no: str
    name: str
    from_station_id: int
    to_station_id: int
    departure_time: time
    arrival_time: time
    duration_minutes: int
    distance_km: int

    from_station: Station
    to_station: Station
    schedules: List["TrainSchedule"]


class TrainSchedule:
    id: int
    train_id: int
    travel_date: date
    status: str

    train: Train
    inventories: List["SeatInventory"]
    tickets: List["Ticket"]


class SeatInventory:
    id: int
    schedule_id: int
    seat_type: str
    total: int
    remaining: int
    price: float

    schedule: TrainSchedule


class Order:
    id: int
    order_no: str
    user_id: int
    status: str
    total_amount: float
    created_at: datetime
    paid_at: Optional[datetime]

    user: User
    tickets: List["Ticket"]
    payments: List["Payment"]
    refunds: List["Refund"]


class Ticket:
    id: int
    order_id: int
    schedule_id: int
    passenger_id: int
    seat_type: str
    seat_no: Optional[str]
    price: float
    status: str

    order: Order
    schedule: TrainSchedule
    passenger: Passenger
    refunds: List["Refund"]
    old_change_records: List["ChangeRecord"]
    new_change_records: List["ChangeRecord"]


class Payment:
    id: int
    order_id: int
    amount: float
    status: str
    payment_no: Optional[str]
    created_at: datetime
    paid_at: Optional[datetime]

    order: Order


class Refund:
    id: int
    order_id: int
    ticket_id: int
    amount: float
    fee: float
    status: str
    created_at: datetime

    order: Order
    ticket: Ticket


class ChangeRecord:
    id: int
    old_ticket_id: int
    new_ticket_id: int
    price_diff: float
    created_at: datetime

    old_ticket: Ticket
    new_ticket: Ticket


class Notification:
    id: int
    user_id: int
    title: str
    content: str
    is_read: bool
    created_at: datetime

    user: User


class AuditLog:
    id: int
    user_id: Optional[int]
    action: str
    detail: Optional[str]
    ip: Optional[str]
    created_at: datetime

    user: Optional[User]
