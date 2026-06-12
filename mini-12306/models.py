from datetime import datetime, date, time

from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    real_name = db.Column(db.String(50), nullable=False)
    id_card = db.Column(db.String(18), unique=True, nullable=False)
    phone = db.Column(db.String(11), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    passengers = db.relationship("Passenger", backref="user", lazy=True)
    orders = db.relationship("Order", backref="user", lazy=True)
    notifications = db.relationship("Notification", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Passenger(db.Model):
    __tablename__ = "passengers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    id_card = db.Column(db.String(18), nullable=False)
    phone = db.Column(db.String(11), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Station(db.Model):
    __tablename__ = "stations"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    city = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)


class Train(db.Model):
    __tablename__ = "trains"

    id = db.Column(db.Integer, primary_key=True)
    train_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    from_station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    to_station_id = db.Column(db.Integer, db.ForeignKey("stations.id"), nullable=False)
    departure_time = db.Column(db.Time, nullable=False)
    arrival_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    distance_km = db.Column(db.Integer, nullable=False)

    from_station = db.relationship("Station", foreign_keys=[from_station_id])
    to_station = db.relationship("Station", foreign_keys=[to_station_id])
    schedules = db.relationship("TrainSchedule", backref="train", lazy=True)


class TrainSchedule(db.Model):
    __tablename__ = "train_schedules"

    id = db.Column(db.Integer, primary_key=True)
    train_id = db.Column(db.Integer, db.ForeignKey("trains.id"), nullable=False)
    travel_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="正常")

    inventories = db.relationship("SeatInventory", backref="schedule", lazy=True)

    __table_args__ = (db.UniqueConstraint("train_id", "travel_date"),)


class SeatInventory(db.Model):
    __tablename__ = "seat_inventories"

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey("train_schedules.id"), nullable=False)
    seat_type = db.Column(db.String(20), nullable=False)
    total = db.Column(db.Integer, nullable=False)
    remaining = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    __table_args__ = (db.UniqueConstraint("schedule_id", "seat_type"),)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(32), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default="待支付")
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)

    tickets = db.relationship("Ticket", backref="order", lazy=True)
    payments = db.relationship("Payment", backref="order", lazy=True)
    refunds = db.relationship("Refund", backref="order", lazy=True)


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey("train_schedules.id"), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey("passengers.id"), nullable=False)
    seat_type = db.Column(db.String(20), nullable=False)
    seat_no = db.Column(db.String(10))
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="待出票")

    schedule = db.relationship("TrainSchedule")
    passenger = db.relationship("Passenger")
    change_records = db.relationship("ChangeRecord", foreign_keys="ChangeRecord.old_ticket_id", backref="old_ticket")


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="待支付")
    payment_no = db.Column(db.String(32), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)


class Refund(db.Model):
    __tablename__ = "refunds"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="处理中")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket = db.relationship("Ticket")


class ChangeRecord(db.Model):
    __tablename__ = "change_records"

    id = db.Column(db.Integer, primary_key=True)
    old_ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    new_ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    price_diff = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    new_ticket = db.relationship("Ticket", foreign_keys=[new_ticket_id])


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(100), nullable=False)
    detail = db.Column(db.Text)
    ip = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
