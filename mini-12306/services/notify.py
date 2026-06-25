from models import Notification
from services.sms import send_sms


def create_notification(db_session, user, title, content):
    notification = Notification(user_id=user.id, title=title, content=content)
    db_session.add(notification)
    send_sms(user.phone, f"{title}: {content}")
    return notification
