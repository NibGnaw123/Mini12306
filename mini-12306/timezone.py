from datetime import date, datetime, timedelta, timezone

APP_TIMEZONE = timezone(timedelta(hours=8), name="CST")


def now() -> datetime:
    """返回东八区当前时间（naive datetime，便于数据库存储与展示）。"""
    return datetime.now(APP_TIMEZONE).replace(tzinfo=None)


def today() -> date:
    """返回东八区当前日期。"""
    return datetime.now(APP_TIMEZONE).date()
