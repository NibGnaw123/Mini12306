#include "ticket_manager.h"
#include <iostream>
#include <iomanip>

std::string TicketManager::generateOrderId() {
    return "ORD" + std::to_string(++orderCounter);
}

TicketManager::TicketManager(std::shared_ptr<TrainManager> tm,
    std::shared_ptr<IPaymentService> pay,
    std::shared_ptr<IMobileService> mob)
    : trainMgr(tm), payment(pay), mobile(mob), orderCounter(10000) {
}

bool TicketManager::buyTicket(const std::string& userId, const std::string& trainNo,
    const std::string& travelDate, int seatCount, std::string& outOrderId) {
    Train* train = trainMgr->getTrain(trainNo);
    if (!train) {
        std::cout << "购票失败: 车次不存在" << std::endl;
        return false;
    }
    if (train->availableSeats < seatCount) {
        std::cout << "购票失败: 余票不足" << std::endl;
        return false;
    }
    double amount = train->price * seatCount;
    std::string orderId = generateOrderId();
    if (!payment->pay(userId, amount, orderId)) {
        std::cout << "购票失败: 支付失败" << std::endl;
        return false;
    }
    if (!trainMgr->deductSeats(trainNo, seatCount)) {
        // 理论上不会失败，但为安全起见回滚支付
        payment->refund(userId, amount, orderId);
        return false;
    }
    TicketOrder order{ orderId, userId, trainNo, travelDate, seatCount, amount, "PAID", "" };
    orders[orderId] = order;
    outOrderId = orderId;
    mobile->sendSMS("用户手机号", "购票成功，订单号:" + orderId);
    std::cout << "购票成功! 订单号: " << orderId << " 金额: " << amount << std::endl;
    return true;
}

bool TicketManager::refundTicket(const std::string& orderId, std::string& outMessage) {
    auto it = orders.find(orderId);
    if (it == orders.end()) {
        outMessage = "订单不存在";
        return false;
    }
    TicketOrder& order = it->second;
    if (order.status != "PAID") {
        outMessage = "订单状态不允许退票";
        return false;
    }
    // 恢复座位
    if (!trainMgr->restoreSeats(order.trainNo, order.seatCount)) {
        outMessage = "系统错误：恢复座位失败";
        return false;
    }
    // 退款
    if (!payment->refund(order.userId, order.amount, orderId)) {
        // 如果退款失败，需要再次扣除座位保持一致性，这里简单处理
        trainMgr->deductSeats(order.trainNo, order.seatCount);
        outMessage = "退款失败";
        return false;
    }
    order.status = "REFUNDED";
    outMessage = "退票成功，退款金额: " + std::to_string(order.amount);
    mobile->sendSMS("用户手机号", "退票成功，订单号:" + orderId);
    return true;
}

bool TicketManager::changeTicket(const std::string& oldOrderId, const std::string& newTrainNo,
    const std::string& newTravelDate, std::string& outNewOrderId) {
    auto oldIt = orders.find(oldOrderId);
    if (oldIt == orders.end() || oldIt->second.status != "PAID") {
        std::cout << "改签失败: 原订单无效或未支付" << std::endl;
        return false;
    }
    TicketOrder& oldOrder = oldIt->second;
    Train* newTrain = trainMgr->getTrain(newTrainNo);
    if (!newTrain) {
        std::cout << "改签失败: 新车次不存在" << std::endl;
        return false;
    }
    if (newTrain->availableSeats < oldOrder.seatCount) {
        std::cout << "改签失败: 新车次余票不足" << std::endl;
        return false;
    }
    double newAmount = newTrain->price * oldOrder.seatCount;
    double diff = newAmount - oldOrder.amount;
    if (diff > 0) {
        // 需要补差价
        if (!payment->pay(oldOrder.userId, diff, "CHANGE_" + oldOrderId)) {
            std::cout << "改签失败: 补差价失败" << std::endl;
            return false;
        }
    }
    else if (diff < 0) {
        // 退还差价
        if (!payment->refund(oldOrder.userId, -diff, "CHANGE_REFUND_" + oldOrderId)) {
            std::cout << "改签失败: 退差价失败" << std::endl;
            return false;
        }
    }
    // 扣除新车次座位，恢复旧车次座位
    if (!trainMgr->deductSeats(newTrainNo, oldOrder.seatCount)) {
        // 回滚差价操作
        if (diff > 0) payment->refund(oldOrder.userId, diff, "CHANGE_" + oldOrderId);
        if (diff < 0) payment->pay(oldOrder.userId, -diff, "CHANGE_REFUND_" + oldOrderId);
        std::cout << "改签失败: 扣除新车次座位失败" << std::endl;
        return false;
    }
    trainMgr->restoreSeats(oldOrder.trainNo, oldOrder.seatCount);
    // 创建新订单
    std::string newOrderId = generateOrderId();
    TicketOrder newOrder{ newOrderId, oldOrder.userId, newTrainNo, newTravelDate,
                         oldOrder.seatCount, newAmount, "PAID", "" };
    orders[newOrderId] = newOrder;
    // 更新旧订单状态
    oldOrder.status = "CHANGED";
    oldOrder.changeToOrderId = newOrderId;
    outNewOrderId = newOrderId;
    mobile->sendSMS("用户手机号", "改签成功，新订单号:" + newOrderId);
    std::cout << "改签成功! 新订单号: " << newOrderId << std::endl;
    return true;
}

void TicketManager::listUserOrders(const std::string& userId) const {
    std::cout << "\n======= 我的订单 =======\n";
    for (const auto& pair : orders) {
        const auto& order = pair.second;
        if (order.userId == userId) {
            std::cout << "订单号: " << order.orderId << " | 车次: " << order.trainNo
                << " | 日期: " << order.travelDate << " | 张数: " << order.seatCount
                << " | 金额: " << order.amount << " | 状态: " << order.status << std::endl;
        }
    }
}