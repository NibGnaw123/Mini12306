#include "user_manager.h"
#include <iostream>

UserManager::UserManager(std::shared_ptr<IIDAuthService> auth, std::shared_ptr<IPaymentService> pay)
    : idAuth(auth), payment(pay) {
}

bool UserManager::registerUser(const std::string& realName, const std::string& idCard,
    const std::string& phone, const std::string& password) {
    if (!idAuth->verify(idCard, realName)) {
        std::cout << "注册失败: 身份证验证不通过" << std::endl;
        return false;
    }
    if (phoneToUserId.find(phone) != phoneToUserId.end()) {
        std::cout << "注册失败: 手机号已注册" << std::endl;
        return false;
    }
    std::string userId = "U" + std::to_string(users.size() + 1000);
    User newUser{ userId, realName, idCard, phone, password };
    users[userId] = newUser;
    phoneToUserId[phone] = userId;
    payment->createAccount(userId, 1000.0);
    std::cout << "注册成功! 用户ID: " << userId << ", 初始余额1000元" << std::endl;
    return true;
}

std::string UserManager::login(const std::string& phone, const std::string& password) {
    auto it = phoneToUserId.find(phone);
    if (it == phoneToUserId.end()) return "";
    const auto& user = users[it->second];
    if (user.password == password) return user.userId;
    return "";
}

User* UserManager::getUser(const std::string& userId) {
    auto it = users.find(userId);
    if (it != users.end()) return &it->second;
    return nullptr;
}