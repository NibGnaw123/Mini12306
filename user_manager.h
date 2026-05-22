#ifndef USER_MANAGER_H
#define USER_MANAGER_H

#include <string>
#include <unordered_map>
#include <memory>
#include "interfaces.h"

struct User {
    std::string userId;
    std::string realName;
    std::string idCard;
    std::string phone;
    std::string password;
};

class UserManager {
private:
    std::unordered_map<std::string, User> users;           // userId -> User
    std::unordered_map<std::string, std::string> phoneToUserId; // phone -> userId
    std::shared_ptr<IIDAuthService> idAuth;
    std::shared_ptr<IPaymentService> payment;
public:
    UserManager(std::shared_ptr<IIDAuthService> auth, std::shared_ptr<IPaymentService> pay);

    bool registerUser(const std::string& realName, const std::string& idCard,
        const std::string& phone, const std::string& password);
    std::string login(const std::string& phone, const std::string& password);
    User* getUser(const std::string& userId);
};

#endif