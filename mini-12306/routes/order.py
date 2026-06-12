from datetime import timedelta

from timezone import now

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    current_app,
)
from sqlalchemy import and_

from extensions import db
from models import (
    Order,
    Ticket,
    Payment,
    Refund,
    ChangeRecord,
    Passenger,
    Train,
    TrainSchedule,
    SeatInventory,
    Notification,
)
from services.payment import create_payment, process_payment, process_refund
from services.notify import create_notification
from utils import (
    login_required,
    generate_order_no,
    generate_seat_no,
    log_action,
    combine_datetime,
)

order_bp = Blueprint("order", __name__)


@order_bp.route("/book/<int:schedule_id>", methods=["GET", "POST"])
@login_required
def book(schedule_id):
    schedule = TrainSchedule.query.get_or_404(schedule_id)
    inventories = SeatInventory.query.filter_by(schedule_id=schedule_id).all()
    passengers = Passenger.query.filter_by(user_id=session["user_id"]).all()

    if request.method == "POST":
        seat_type = request.form.get("seat_type")
        passenger_id = request.form.get("passenger_id")

        if not seat_type or not passenger_id:
            flash("请选择席别和乘车人", "warning")
            return render_template(
                "order/book.html",
                schedule=schedule,
                inventories=inventories,
                passengers=passengers,
            )

        passenger = Passenger.query.filter_by(
            id=passenger_id, user_id=session["user_id"]
        ).first()
        if not passenger:
            flash("乘车人不存在", "danger")
            return redirect(url_for("train.detail", schedule_id=schedule_id))

        inventory = SeatInventory.query.filter_by(
            schedule_id=schedule_id, seat_type=seat_type
        ).with_for_update().first()

        if not inventory or inventory.remaining <= 0:
            flash("余票不足", "danger")
            return redirect(url_for("train.detail", schedule_id=schedule_id))

        order = Order(
            order_no=generate_order_no(),
            user_id=session["user_id"],
            status="待支付",
            total_amount=inventory.price,
        )
        db.session.add(order)
        db.session.flush()

        ticket = Ticket(
            order_id=order.id,
            schedule_id=schedule_id,
            passenger_id=passenger.id,
            seat_type=seat_type,
            price=inventory.price,
            status="待出票",
        )
        db.session.add(ticket)

        pay_info = create_payment(inventory.price)
        payment = Payment(
            order_id=order.id,
            amount=inventory.price,
            status="待支付",
            payment_no=pay_info["payment_no"],
        )
        db.session.add(payment)
        log_action(session["user_id"], "创建订单", order.order_no)
        db.session.commit()

        return redirect(url_for("order.pay", order_id=order.id))

    return render_template(
        "order/book.html",
        schedule=schedule,
        inventories=inventories,
        passengers=passengers,
    )


@order_bp.route("/pay/<int:order_id>", methods=["GET", "POST"])
@login_required
def pay(order_id):
    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first_or_404()
    payment = Payment.query.filter_by(order_id=order.id, status="待支付").first()

    if order.status != "待支付":
        flash("订单状态不允许支付", "warning")
        return redirect(url_for("order.my_orders"))

    if request.method == "POST":
        if not payment:
            flash("支付记录不存在", "danger")
            return redirect(url_for("order.my_orders"))

        inventory = SeatInventory.query.filter(
            and_(
                SeatInventory.schedule_id == order.tickets[0].schedule_id,
                SeatInventory.seat_type == order.tickets[0].seat_type,
            )
        ).with_for_update().first()

        if not inventory or inventory.remaining <= 0:
            flash("余票不足，支付失败", "danger")
            return redirect(url_for("order.my_orders"))

        result = process_payment(payment.payment_no, payment.amount)
        payment.status = "支付成功"
        payment.paid_at = result["paid_at"]
        order.status = "已支付"
        order.paid_at = result["paid_at"]

        inventory.remaining -= 1
        sold = inventory.total - inventory.remaining
        for ticket in order.tickets:
            ticket.seat_no = generate_seat_no(ticket.seat_type, sold)
            ticket.status = "已出票"
        order.status = "已出票"

        user = order.user
        create_notification(
            db.session,
            user,
            "支付成功",
            f"订单 {order.order_no} 支付成功，车票已出票",
        )
        log_action(session["user_id"], "订单支付", order.order_no)
        db.session.commit()
        flash("支付成功，车票已出票", "success")
        return redirect(url_for("order.my_orders"))

    return render_template("order/pay.html", order=order, payment=payment)


@order_bp.route("/my")
@login_required
def my_orders():
    status_filter = request.args.get("status", "")
    query = Order.query.filter_by(user_id=session["user_id"])
    if status_filter:
        query = query.filter_by(status=status_filter)
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template("order/my_orders.html", orders=orders, status_filter=status_filter)


@order_bp.route("/detail/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.filter_by(id=order_id, user_id=session["user_id"]).first_or_404()
    return render_template("order/detail.html", order=order)


@order_bp.route("/refund/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def refund(ticket_id):
    ticket = (
        Ticket.query.join(Order)
        .filter(Ticket.id == ticket_id, Order.user_id == session["user_id"])
        .first_or_404()
    )

    if ticket.status != "已出票":
        flash("该车票不可退票", "warning")
        return redirect(url_for("order.my_orders"))

    schedule = ticket.schedule
    train = schedule.train
    depart_dt = combine_datetime(schedule.travel_date, train.departure_time)
    if now() > depart_dt - timedelta(hours=2):
        flash("发车前2小时内不可退票", "danger")
        return redirect(url_for("order.my_orders"))

    if request.method == "POST":
        fee_rate = current_app.config["REFUND_FEE_RATE"]
        fee = round(ticket.price * fee_rate, 2)
        refund_amount = round(ticket.price - fee, 2)

        inventory = SeatInventory.query.filter_by(
            schedule_id=ticket.schedule_id, seat_type=ticket.seat_type
        ).with_for_update().first()
        if inventory:
            inventory.remaining += 1

        ticket.status = "已退票"
        ticket.order.status = "已退票"

        refund_record = Refund(
            order_id=ticket.order_id,
            ticket_id=ticket.id,
            amount=refund_amount,
            fee=fee,
            status="退款成功",
        )
        db.session.add(refund_record)
        process_refund(refund_amount)

        create_notification(
            db.session,
            ticket.order.user,
            "退票成功",
            f"车票 {ticket.seat_no} 已退票，退款 ¥{refund_amount:.2f}（手续费 ¥{fee:.2f}）",
        )
        log_action(session["user_id"], "退票", f"票号 {ticket.id}")
        db.session.commit()
        flash(f"退票成功，退款 ¥{refund_amount:.2f}", "success")
        return redirect(url_for("order.my_orders"))

    fee_rate = current_app.config["REFUND_FEE_RATE"]
    fee = round(ticket.price * fee_rate, 2)
    refund_amount = round(ticket.price - fee, 2)
    return render_template(
        "order/refund.html", ticket=ticket, fee=fee, refund_amount=refund_amount
    )


@order_bp.route("/change/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def change(ticket_id):
    ticket = (
        Ticket.query.join(Order)
        .filter(Ticket.id == ticket_id, Order.user_id == session["user_id"])
        .first_or_404()
    )

    if ticket.status != "已出票":
        flash("该车票不可改签", "warning")
        return redirect(url_for("order.my_orders"))

    schedule = ticket.schedule
    train = schedule.train
    depart_dt = combine_datetime(schedule.travel_date, train.departure_time)
    if now() > depart_dt - timedelta(
        hours=current_app.config["CHANGE_DEADLINE_HOURS"]
    ):
        flash("发车前2小时内不可改签", "danger")
        return redirect(url_for("order.my_orders"))

    available_schedules = (
        TrainSchedule.query.join(Train)
        .filter(
            TrainSchedule.travel_date >= schedule.travel_date,
            TrainSchedule.status == "正常",
            Train.from_station_id == train.from_station_id,
            Train.to_station_id == train.to_station_id,
            TrainSchedule.id != schedule.id,
        )
        .all()
    )

    if request.method == "POST":
        new_schedule_id = request.form.get("new_schedule_id")
        if not new_schedule_id:
            flash("请选择新车次", "warning")
            return render_template(
                "order/change.html", ticket=ticket, schedules=available_schedules
            )

        new_schedule = TrainSchedule.query.get(new_schedule_id)
        inventory = SeatInventory.query.filter_by(
            schedule_id=new_schedule_id, seat_type=ticket.seat_type
        ).with_for_update().first()

        if not inventory or inventory.remaining <= 0:
            flash("新车次余票不足", "danger")
            return render_template(
                "order/change.html", ticket=ticket, schedules=available_schedules
            )

        price_diff = round(inventory.price - ticket.price, 2)

        old_inventory = SeatInventory.query.filter_by(
            schedule_id=ticket.schedule_id, seat_type=ticket.seat_type
        ).with_for_update().first()
        if old_inventory:
            old_inventory.remaining += 1

        inventory.remaining -= 1
        sold = inventory.total - inventory.remaining

        ticket.status = "已改签"
        ticket.order.status = "已改签"

        new_order = Order(
            order_no=generate_order_no(),
            user_id=session["user_id"],
            status="已出票",
            total_amount=inventory.price,
            paid_at=now(),
        )
        db.session.add(new_order)
        db.session.flush()

        new_ticket = Ticket(
            order_id=new_order.id,
            schedule_id=new_schedule_id,
            passenger_id=ticket.passenger_id,
            seat_type=ticket.seat_type,
            seat_no=generate_seat_no(ticket.seat_type, sold),
            price=inventory.price,
            status="已出票",
        )
        db.session.add(new_ticket)
        db.session.flush()

        change_record = ChangeRecord(
            old_ticket_id=ticket.id,
            new_ticket_id=new_ticket.id,
            price_diff=price_diff,
        )
        db.session.add(change_record)

        if price_diff > 0:
            process_payment(f"CHG{new_order.order_no}", price_diff)
            msg = f"改签成功，需补差价 ¥{price_diff:.2f}"
        elif price_diff < 0:
            process_refund(abs(price_diff))
            msg = f"改签成功，退还差价 ¥{abs(price_diff):.2f}"
        else:
            msg = "改签成功，无差价"

        create_notification(db.session, ticket.order.user, "改签成功", msg)
        log_action(session["user_id"], "改签", f"原票 {ticket.id} -> 新票 {new_ticket.id}")
        db.session.commit()
        flash(msg, "success")
        return redirect(url_for("order.my_orders"))

    return render_template(
        "order/change.html", ticket=ticket, schedules=available_schedules
    )


@order_bp.route("/passengers", methods=["GET", "POST"])
@login_required
def passengers():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        id_card = request.form.get("id_card", "").strip().upper()
        phone = request.form.get("phone", "").strip()

        if not all([name, id_card, phone]):
            flash("请填写完整信息", "warning")
        else:
            p = Passenger(
                user_id=session["user_id"], name=name, id_card=id_card, phone=phone
            )
            db.session.add(p)
            log_action(session["user_id"], "添加乘车人", name)
            db.session.commit()
            flash("乘车人添加成功", "success")
        return redirect(url_for("order.passengers"))

    passengers_list = Passenger.query.filter_by(user_id=session["user_id"]).all()
    return render_template("order/passengers.html", passengers=passengers_list)


@order_bp.route("/notifications")
@login_required
def notifications():
    notes = (
        Notification.query.filter_by(user_id=session["user_id"])
        .order_by(Notification.created_at.desc())
        .all()
    )
    Notification.query.filter_by(user_id=session["user_id"], is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()
    return render_template("order/notifications.html", notifications=notes)
