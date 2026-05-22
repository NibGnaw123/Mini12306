#ifndef INTERFACES_H
#define INTERFACES_H

#include <string>

// 身份证认证服务抽象接口
class IIDAuthService {
public:
    virtual ~IIDAuthService() = default;
    virtual bool verify(const std::string& idCard, const std::string& realName) = 0;
};

// 移动服务抽象接口（短信通知）
class IMobileService {
public:
    virtual ~IMobileService() = default;
    virtual bool sendSMS(const std::string& phone, const std::string& message) = 0;
};

// 在线支付服务抽象接口
class IPaymentService {
public:
    virtual ~IPaymentService() = default;
    virtual bool createAccount(const std::string& userId, double initialBalance) = 0;
    virtual bool pay(const std::string& userId, double amount, const std::string& orderId) = 0;
    virtual bool refund(const std::string& userId, double amount, const std::string& orderId) = 0;
};

#endif
