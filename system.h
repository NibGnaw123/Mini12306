#ifndef SYSTEM_H
#define SYSTEM_H

#include <memory>
#include "user_manager.h"
#include "train_manager.h"
#include "ticket_manager.h"
#include "mock_services.h"

class System {
private:
    std::shared_ptr<MockIDAuthService> idAuth;
    std::shared_ptr<MockMobileService> mobile;
    std::shared_ptr<MockPaymentService> payment;
    std::shared_ptr<UserManager> userMgr;
    std::shared_ptr<TrainManager> trainMgr;
    std::shared_ptr<TicketManager> ticketMgr;

    std::string currentUserId;  // 当前登录用户ID，空表示未登录

public:
    System();
    void start();   // 主循环
private:
    void mainMenu();
    void loginUI();
    void registerUI();
    void userMenu();
    void adminMenu();
    // 用户功能
    void searchTrainsUI();
    void buyTicketUI();
    void refundTicketUI();
    void changeTicketUI();
    void listOrdersUI();
    // 管理员功能
    void addTrainUI();
    void updateTrainUI();
};

#endif