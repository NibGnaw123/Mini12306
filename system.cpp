#include "system.h"
#include <iostream>
#include <limits>

System::System() {
    idAuth = std::make_shared<MockIDAuthService>();
    mobile = std::make_shared<MockMobileService>();
    payment = std::make_shared<MockPaymentService>();
    userMgr = std::make_shared<UserManager>(idAuth, payment);
    trainMgr = std::make_shared<TrainManager>();
    ticketMgr = std::make_shared<TicketManager>(trainMgr, payment, mobile);
    currentUserId = "";
}

void System::start() {
    int choice;
    while (true) {
        mainMenu();
        std::cin >> choice;
        if (choice == 1) loginUI();
        else if (choice == 2) registerUI();
        else if (choice == 3) {
            std::cout << "谢谢使用，再见！" << std::endl;
            break;
        }
        else {
            std::cout << "无效输入，请重新选择。" << std::endl;
        }
    }
}

void System::mainMenu() {
    std::cout << "\n========== Mini-12306 主菜单 ==========\n";
    std::cout << "1. 登录\n";
    std::cout << "2. 注册\n";
    std::cout << "3. 退出\n";
    std::cout << "请选择: ";
}

void System::loginUI() {
    std::string phone, pwd;
    std::cout << "手机号: ";
    std::cin >> phone;
    std::cout << "密码: ";
    std::cin >> pwd;
    std::string userId = userMgr->login(phone, pwd);
    if (userId.empty()) {
        std::cout << "登录失败，手机号或密码错误。" << std::endl;
        return;
    }
    currentUserId = userId;
    User* user = userMgr->getUser(userId);
    std::cout << "登录成功！欢迎 " << user->realName << std::endl;
    // 判断是否是管理员（这里简单用用户ID是否为"ADMIN"判断，可扩展）
    if (currentUserId == "ADMIN") {
        adminMenu();
    }
    else {
        userMenu();
    }
    currentUserId = ""; // 退出后清空
}

void System::registerUI() {
    std::string name, idCard, phone, pwd;
    std::cout << "真实姓名: ";
    std::cin >> name;
    std::cout << "身份证号: ";
    std::cin >> idCard;
    std::cout << "手机号: ";
    std::cin >> phone;
    std::cout << "密码: ";
    std::cin >> pwd;
    userMgr->registerUser(name, idCard, phone, pwd);
}

void System::userMenu() {
    int choice;
    while (true) {
        std::cout << "\n====== 用户功能菜单 ======\n";
        std::cout << "1. 查询车次\n";
        std::cout << "2. 购票\n";
        std::cout << "3. 退票\n";
        std::cout << "4. 改签\n";
        std::cout << "5. 我的订单\n";
        std::cout << "6. 退出登录\n";
        std::cout << "请选择: ";
        std::cin >> choice;
        switch (choice) {
        case 1: searchTrainsUI(); break;
        case 2: buyTicketUI(); break;
        case 3: refundTicketUI(); break;
        case 4: changeTicketUI(); break;
        case 5: listOrdersUI(); break;
        case 6: return;
        default: std::cout << "无效选择。" << std::endl;
        }
    }
}

void System::adminMenu() {
    int choice;
    while (true) {
        std::cout << "\n====== 管理员菜单 ======\n";
        std::cout << "1. 添加车次\n";
        std::cout << "2. 修改车次（价格/总座位）\n";
        std::cout << "3. 退出登录\n";
        std::cout << "请选择: ";
        std::cin >> choice;
        if (choice == 1) addTrainUI();
        else if (choice == 2) updateTrainUI();
        else if (choice == 3) return;
        else std::cout << "无效选择。" << std::endl;
    }
}

// ----- 用户功能实现 -----
void System::searchTrainsUI() {
    std::string from, to;
    std::cout << "出发地: ";
    std::cin >> from;
    std::cout << "目的地: ";
    std::cin >> to;
    auto trains = trainMgr->searchTrains(from, to);
    if (trains.empty()) {
        std::cout << "未找到符合条件的车次。" << std::endl;
    }
    else {
        std::cout << "\n车次\t出发地\t目的地\t发时\t到时\t票价\t余票\n";
        for (const auto& t : trains) {
            std::cout << t.trainNo << "\t" << t.departure << "\t" << t.destination
                << "\t" << t.depTime << "\t" << t.arrTime << "\t"
                << t.price << "\t" << t.availableSeats << std::endl;
        }
    }
}

void System::buyTicketUI() {
    std::string trainNo, travelDate;
    int seatCount;
    std::cout << "车次号: ";
    std::cin >> trainNo;
    std::cout << "乘车日期(YYYY-MM-DD): ";
    std::cin >> travelDate;
    std::cout << "购票数量: ";
    std::cin >> seatCount;
    std::string orderId;
    if (ticketMgr->buyTicket(currentUserId, trainNo, travelDate, seatCount, orderId)) {
        std::cout << "购票成功，订单号: " << orderId << std::endl;
    }
    else {
        std::cout << "购票失败，请检查车次或余额。" << std::endl;
    }
}

void System::refundTicketUI() {
    std::string orderId;
    std::cout << "要退票的订单号: ";
    std::cin >> orderId;
    std::string msg;
    if (ticketMgr->refundTicket(orderId, msg)) {
        std::cout << msg << std::endl;
    }
    else {
        std::cout << "退票失败: " << msg << std::endl;
    }
}

void System::changeTicketUI() {
    std::string oldOrderId, newTrainNo, newDate;
    std::cout << "原订单号: ";
    std::cin >> oldOrderId;
    std::cout << "新车次号: ";
    std::cin >> newTrainNo;
    std::cout << "新乘车日期: ";
    std::cin >> newDate;
    std::string newOrderId;
    if (ticketMgr->changeTicket(oldOrderId, newTrainNo, newDate, newOrderId)) {
        std::cout << "改签成功，新订单号: " << newOrderId << std::endl;
    }
    else {
        std::cout << "改签失败。" << std::endl;
    }
}

void System::listOrdersUI() {
    ticketMgr->listUserOrders(currentUserId);
}

// ----- 管理员功能实现 -----
void System::addTrainUI() {
    Train t;
    std::cout << "车次号: ";
    std::cin >> t.trainNo;
    std::cout << "出发地: ";
    std::cin >> t.departure;
    std::cout << "目的地: ";
    std::cin >> t.destination;
    std::cout << "发时(HH:MM): ";
    std::cin >> t.depTime;
    std::cout << "到时(HH:MM): ";
    std::cin >> t.arrTime;
    std::cout << "票价: ";
    std::cin >> t.price;
    std::cout << "总座位数: ";
    std::cin >> t.totalSeats;
    t.availableSeats = t.totalSeats;
    if (trainMgr->addTrain(t)) {
        std::cout << "添加车次成功。" << std::endl;
    }
    else {
        std::cout << "添加失败，车次号可能已存在。" << std::endl;
    }
}

void System::updateTrainUI() {
    std::string trainNo;
    double newPrice;
    int newSeats;
    std::cout << "要修改的车次号: ";
    std::cin >> trainNo;
    std::cout << "新票价: ";
    std::cin >> newPrice;
    std::cout << "新总座位数: ";
    std::cin >> newSeats;
    if (trainMgr->updateTrain(trainNo, newPrice, newSeats)) {
        std::cout << "修改成功。" << std::endl;
    }
    else {
        std::cout << "修改失败，车次不存在。" << std::endl;
    }
}