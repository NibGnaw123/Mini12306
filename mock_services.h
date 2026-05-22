#ifndef MOCK_SERVICES_H
#define MOCK_SERVICES_H

#include "interfaces.h"
#include <unordered_map>

class MockIDAuthService : public IIDAuthService {
public:
    bool verify(const std::string& idCard, const std::string& realName) override;
};

class MockMobileService : public IMobileService {
public:
    bool sendSMS(const std::string& phone, const std::string& message) override;
};

class MockPaymentService : public IPaymentService {
private:
    std::unordered_map<std::string, double> accounts; // userId -> ”‡∂Ó
public:
    bool createAccount(const std::string& userId, double initialBalance) override;
    bool pay(const std::string& userId, double amount, const std::string& orderId) override;
    bool refund(const std::string& userId, double amount, const std::string& orderId) override;
};

#endif