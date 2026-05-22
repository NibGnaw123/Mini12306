#include "mock_services.h"
#include <iostream>

bool MockIDAuthService::verify(const std::string& idCard, const std::string& realName) {
    // 简单模拟：身份证非空且姓名长度>=2即通过
    return !idCard.empty() && realName.length() >= 2;
}

bool MockMobileService::sendSMS(const std::string& phone, const std::string& message) {
    std::cout << "[短信发送] 手机号: " << phone << " 内容: " << message << std::endl;
    return true;
}

bool MockPaymentService::createAccount(const std::string& userId, double initialBalance) {
    if (accounts.find(userId) != accounts.end()) return false;
    accounts[userId] = initialBalance;
    std::cout << "[支付服务] 为用户 " << userId << " 创建账户，初始余额: " << initialBalance << std::endl;
    return true;
}

bool MockPaymentService::pay(const std::string& userId, double amount, const std::string& orderId) {
    auto it = accounts.find(userId);
    if (it == accounts.end() || it->second < amount) {
        std::cout << "[支付服务] 支付失败: 余额不足或账户不存在" << std::endl;
        return false;
    }
    it->second -= amount;
    std::cout << "[支付服务] 支付成功: 用户 " << userId << " 金额 " << amount
        << " 订单 " << orderId << " 剩余余额: " << it->second << std::endl;
    return true;
}

bool MockPaymentService::refund(const std::string& userId, double amount, const std::string& orderId) {
    auto it = accounts.find(userId);
    if (it == accounts.end()) {
        std::cout << "[支付服务] 退款失败: 账户不存在" << std::endl;
        return false;
    }
    it->second += amount;
    std::cout << "[支付服务] 退款成功: 用户 " << userId << " 金额 " << amount
        << " 订单 " << orderId << " 当前余额: " << it->second << std::endl;
    return true;
}