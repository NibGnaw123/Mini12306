from datetime import date, time, timedelta

from extensions import db
from models import User, Station, Train, TrainSchedule, SeatInventory, Passenger

SEAT_TYPES = [
    ("二等座", 200, 553.5),
    ("一等座", 80, 933.5),
    ("硬卧", 120, 650.0),
    ("软卧", 40, 1050.0),
]

STATIONS = [
    ("北京南", "北京", "BJN"),
    ("上海虹桥", "上海", "SHH"),
    ("广州南", "广州", "GZN"),
    ("深圳北", "深圳", "SZB"),
    ("杭州东", "杭州", "HZD"),
    ("南京南", "南京", "NJN"),
    ("武汉", "武汉", "WHN"),
    ("成都东", "成都", "CDD"),
]

TRAINS = [
    ("G1", "北京南-上海虹桥", "北京南", "上海虹桥", "09:00", "13:28", 268, 1318),
    ("G3", "北京南-上海虹桥", "北京南", "上海虹桥", "14:00", "18:28", 268, 1318),
    ("G7", "北京南-广州南", "北京南", "广州南", "08:00", "16:30", 510, 2298),
    ("G13", "上海虹桥-杭州东", "上海虹桥", "杭州东", "07:30", "08:15", 45, 159),
    ("G15", "上海虹桥-南京南", "上海虹桥", "南京南", "10:00", "11:20", 80, 301),
    ("G21", "广州南-深圳北", "广州南", "深圳北", "09:00", "09:35", 35, 102),
    ("G25", "武汉-成都东", "武汉", "成都东", "08:30", "14:00", 330, 1223),
    ("G31", "南京南-杭州东", "南京南", "杭州东", "13:00", "14:10", 70, 256),
]


def seed_database():
    if User.query.filter_by(username="admin").first():
        return

    admin = User(
        username="admin",
        real_name="系统管理员",
        id_card="110101199001011234",
        phone="13800000000",
        is_admin=True,
    )
    admin.set_password("admin123")
    db.session.add(admin)

    demo = User(
        username="demo",
        real_name="张三",
        id_card="320102199505051234",
        phone="13900001111",
    )
    demo.set_password("demo123")
    db.session.add(demo)
    db.session.flush()
    db.session.add(
        Passenger(
            user_id=demo.id,
            name="张三",
            id_card="320102199505051234",
            phone="13900001111",
        )
    )

    station_map = {}
    for name, city, code in STATIONS:
        s = Station(name=name, city=city, code=code)
        db.session.add(s)
        db.session.flush()
        station_map[name] = s

    train_objs = []
    for train_no, name, from_name, to_name, dep, arr, dur, dist in TRAINS:
        t = Train(
            train_no=train_no,
            name=name,
            from_station_id=station_map[from_name].id,
            to_station_id=station_map[to_name].id,
            departure_time=time(*map(int, dep.split(":"))),
            arrival_time=time(*map(int, arr.split(":"))),
            duration_minutes=dur,
            distance_km=dist,
        )
        db.session.add(t)
        db.session.flush()
        train_objs.append(t)

    today = date.today()
    for day_offset in range(14):
        travel_date = today + timedelta(days=day_offset)
        for train in train_objs:
            schedule = TrainSchedule(train_id=train.id, travel_date=travel_date)
            db.session.add(schedule)
            db.session.flush()
            for seat_type, total, price in SEAT_TYPES:
                db.session.add(
                    SeatInventory(
                        schedule_id=schedule.id,
                        seat_type=seat_type,
                        total=total,
                        remaining=total,
                        price=price,
                    )
                )

    db.session.commit()
