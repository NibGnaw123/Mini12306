import os

os.environ.setdefault("TZ", "Asia/Shanghai")

from flask import Flask, flash, redirect, request, session, url_for

from config import Config
from extensions import db
from models import Notification
from routes import register_blueprints
from seed import seed_database


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    register_blueprints(app)

    public_endpoints = {"auth.login", "auth.register", "static"}

    @app.before_request
    def require_login():
        if request.endpoint in public_endpoints:
            return
        if "user_id" not in session:
            flash("请先登录", "warning")
            return redirect(url_for("auth.login", next=request.url))

    @app.context_processor
    def inject_notifications():
        unread = 0
        if session.get("user_id"):
            unread = Notification.query.filter_by(
                user_id=session["user_id"], is_read=False
            ).count()
        return dict(unread=unread)

    with app.app_context():
        db.create_all()
        seed_database()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
