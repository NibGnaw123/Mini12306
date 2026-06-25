from datetime import time, timedelta

from config import Config
from extensions import db
from timezone import today as get_today
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

# train_no, name, from_station, to_station, dep, arr, duration_minutes, distance_km
TRAINS = [
    # 京沪
    ("G1", "北京南-上海虹桥", "北京南", "上海虹桥", "09:00", "13:28", 268, 1318),
    ("G3", "北京南-上海虹桥", "北京南", "上海虹桥", "14:00", "18:28", 268, 1318),
    ("G5", "北京南-上海虹桥", "北京南", "上海虹桥", "11:00", "15:28", 268, 1318),
    ("G9", "北京南-上海虹桥", "北京南", "上海虹桥", "17:00", "21:28", 268, 1318),
    ("G2", "上海虹桥-北京南", "上海虹桥", "北京南", "07:00", "11:28", 268, 1318),
    ("G4", "上海虹桥-北京南", "上海虹桥", "北京南", "12:00", "16:28", 268, 1318),
    ("G6", "上海虹桥-北京南", "上海虹桥", "北京南", "18:00", "22:28", 268, 1318),
    # 京广
    ("G7", "北京南-广州南", "北京南", "广州南", "08:00", "16:30", 510, 2298),
    ("G17", "北京南-广州南", "北京南", "广州南", "13:00", "21:30", 510, 2298),
    ("G80", "广州南-北京南", "广州南", "北京南", "08:00", "16:30", 510, 2298),
    # 沪广 / 沪深
    ("G99", "上海虹桥-广州南", "上海虹桥", "广州南", "08:00", "15:30", 450, 1790),
    ("G100", "广州南-上海虹桥", "广州南", "上海虹桥", "09:00", "16:30", 450, 1790),
    ("G997", "上海虹桥-深圳北", "上海虹桥", "深圳北", "08:30", "16:00", 450, 1680),
    ("G998", "深圳北-上海虹桥", "深圳北", "上海虹桥", "07:30", "15:00", 450, 1680),
    # 京汉 / 武广
    ("G67", "北京南-武汉", "北京南", "武汉", "09:30", "14:20", 290, 1226),
    ("G69", "北京南-武汉", "北京南", "武汉", "15:00", "19:50", 290, 1226),
    ("G68", "武汉-北京南", "武汉", "北京南", "08:00", "12:50", 290, 1226),
    # 京成
    ("G89", "北京南-成都东", "北京南", "成都东", "06:53", "14:38", 465, 1874),
    ("G90", "成都东-北京南", "成都东", "北京南", "08:00", "15:45", 465, 1874),
    # 沪宁 / 沪杭 / 宁杭
    ("G13", "上海虹桥-杭州东", "上海虹桥", "杭州东", "07:30", "08:15", 45, 159),
    ("G7351", "上海虹桥-杭州东", "上海虹桥", "杭州东", "12:00", "12:45", 45, 159),
    ("G7353", "上海虹桥-杭州东", "上海虹桥", "杭州东", "18:30", "19:15", 45, 159),
    ("G7352", "杭州东-上海虹桥", "杭州东", "上海虹桥", "08:00", "08:45", 45, 159),
    ("G7354", "杭州东-上海虹桥", "杭州东", "上海虹桥", "16:00", "16:45", 45, 159),
    ("G15", "上海虹桥-南京南", "上海虹桥", "南京南", "10:00", "11:20", 80, 301),
    ("G7001", "上海虹桥-南京南", "上海虹桥", "南京南", "14:30", "15:50", 80, 301),
    ("G7003", "上海虹桥-南京南", "上海虹桥", "南京南", "19:00", "20:20", 80, 301),
    ("G7002", "南京南-上海虹桥", "南京南", "上海虹桥", "07:00", "08:20", 80, 301),
    ("G7004", "南京南-上海虹桥", "南京南", "上海虹桥", "16:30", "17:50", 80, 301),
    ("G31", "南京南-杭州东", "南京南", "杭州东", "13:00", "14:10", 70, 256),
    ("G7631", "南京南-杭州东", "南京南", "杭州东", "08:30", "09:40", 70, 256),
    ("G7633", "南京南-杭州东", "南京南", "杭州东", "17:00", "18:10", 70, 256),
    ("G7632", "杭州东-南京南", "杭州东", "南京南", "10:00", "11:10", 70, 256),
    # 京宁 / 京杭
    ("G101", "北京南-南京南", "北京南", "南京南", "10:00", "13:30", 210, 1023),
    ("G102", "南京南-北京南", "南京南", "北京南", "14:00", "17:30", 210, 1023),
    ("G39", "北京南-杭州东", "北京南", "杭州东", "11:30", "16:00", 270, 1279),
    ("G40", "杭州东-北京南", "杭州东", "北京南", "09:00", "13:30", 270, 1279),
    # 广深
    ("G21", "广州南-深圳北", "广州南", "深圳北", "09:00", "09:35", 35, 102),
    ("G6221", "广州南-深圳北", "广州南", "深圳北", "14:00", "14:35", 35, 102),
    ("G6223", "广州南-深圳北", "广州南", "深圳北", "19:00", "19:35", 35, 102),
    ("G6222", "深圳北-广州南", "深圳北", "广州南", "10:00", "10:35", 35, 102),
    # 武成 / 武宁 / 武杭
    ("G25", "武汉-成都东", "武汉", "成都东", "08:30", "14:00", 330, 1223),
    ("G855", "武汉-成都东", "武汉", "成都东", "15:00", "20:30", 330, 1223),
    ("G856", "成都东-武汉", "成都东", "武汉", "09:00", "14:30", 330, 1223),
    ("G1721", "南京南-武汉", "南京南", "武汉", "11:00", "13:30", 150, 520),
    ("G1723", "南京南-武汉", "南京南", "武汉", "18:00", "20:30", 150, 520),
    ("G1722", "武汉-南京南", "武汉", "南京南", "08:30", "11:00", 150, 520),
    ("G595", "杭州东-武汉", "杭州东", "武汉", "09:00", "12:30", 210, 780),
    ("G596", "武汉-杭州东", "武汉", "杭州东", "13:00", "16:30", 210, 780),
    # 成广
    ("G291", "广州南-成都东", "广州南", "成都东", "08:00", "15:30", 450, 1500),
    ("G292", "成都东-广州南", "成都东", "广州南", "07:00", "14:30", 450, 1500),
    # 武广 / 广武
    ("G1101", "武汉-广州南", "武汉", "广州南", "09:00", "13:20", 260, 1069),
    ("G1102", "广州南-武汉", "广州南", "武汉", "14:00", "18:20", 260, 1069),
    # 成渝（经武汉中转段模拟直达）
    ("G2201", "成都东-深圳北", "成都东", "深圳北", "07:30", "16:00", 510, 1600),
    ("G2202", "深圳北-成都东", "深圳北", "成都东", "08:00", "16:30", 510, 1600),
]


def _seed_users():
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


def _ensure_stations():
    station_map = {}
    for name, city, code in STATIONS:
        station = Station.query.filter_by(name=name).first()
        if not station:
            station = Station(name=name, city=city, code=code)
            db.session.add(station)
            db.session.flush()
        station_map[name] = station
    return station_map


def _create_schedules(train):
    today = get_today()
    for day_offset in range(Config.SCHEDULE_DAYS):
        travel_date = today + timedelta(days=day_offset)
        exists = TrainSchedule.query.filter_by(
            train_id=train.id, travel_date=travel_date
        ).first()
        if exists:
            continue
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


def _ensure_trains(station_map):
    existing_nos = {t.train_no for t in Train.query.all()}
    for train_no, name, from_name, to_name, dep, arr, dur, dist in TRAINS:
        if train_no in existing_nos:
            continue
        train = Train(
            train_no=train_no,
            name=name,
            from_station_id=station_map[from_name].id,
            to_station_id=station_map[to_name].id,
            departure_time=time(*map(int, dep.split(":"))),
            arrival_time=time(*map(int, arr.split(":"))),
            duration_minutes=dur,
            distance_km=dist,
        )
        db.session.add(train)
        db.session.flush()
        _create_schedules(train)


def seed_database():
    if not User.query.filter_by(username="admin").first():
        _seed_users()

    station_map = _ensure_stations()
    _ensure_trains(station_map)
    for train in Train.query.all():
        _create_schedules(train)
    db.session.commit()
