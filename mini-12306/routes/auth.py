from urllib.parse import urlparse, urljoin

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from extensions import db
from models import User, Passenger
from services.id_verify import verify_identity
from services.notify import create_notification
from utils import log_action

auth_bp = Blueprint("auth", __name__)


def _is_safe_redirect(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


def _redirect_after_login(user):
    next_url = request.args.get("next") or request.form.get("next")
    if _is_safe_redirect(next_url):
        return redirect(next_url)
    if user.is_admin:
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("main.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        real_name = request.form.get("real_name", "").strip()
        id_card = request.form.get("id_card", "").strip().upper()
        phone = request.form.get("phone", "").strip()

        if User.query.filter((User.username == username) | (User.id_card == id_card)).first():
            flash("用户名或身份证号已存在", "danger")
            return render_template("auth/register.html")

        ok, msg = verify_identity(real_name, id_card, phone)
        if not ok:
            flash(msg, "danger")
            return render_template("auth/register.html")

        user = User(username=username, real_name=real_name, id_card=id_card, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        db.session.add(
            Passenger(user_id=user.id, name=real_name, id_card=id_card, phone=phone)
        )
        create_notification(db.session, user, "注册成功", "欢迎加入 Mini-12306")
        log_action(user.id, "用户注册", f"用户名: {username}")
        db.session.commit()

        flash("注册成功，请登录", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        user = User.query.get(session["user_id"])
        if user:
            return _redirect_after_login(user)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash("用户名或密码错误", "danger")
            return render_template("auth/login.html")

        session["user_id"] = user.id
        session["username"] = user.username
        session["is_admin"] = user.is_admin
        log_action(user.id, "用户登录")
        db.session.commit()
        flash("登录成功", "success")
        return _redirect_after_login(user)

    return render_template("auth/login.html", next=request.args.get("next", ""))


@auth_bp.route("/logout")
def logout():
    user_id = session.get("user_id")
    if user_id:
        log_action(user_id, "用户登出")
        db.session.commit()
    session.clear()
    flash("已退出登录", "info")
    return redirect(url_for("auth.login"))
