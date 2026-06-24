import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    TIMEZONE = "Asia/Shanghai"
    SECRET_KEY = os.environ.get("SECRET_KEY", "mini-12306-dev-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'mini12306.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REFUND_FEE_RATE = 0.05
    CHANGE_DEADLINE_HOURS = 2
    SCHEDULE_DAYS = 15
