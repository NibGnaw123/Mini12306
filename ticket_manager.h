#ifndef TICKET_MANAGER_H
#define TICKET_MANAGER_H

#include <string>
#include <unordered_map>
#include <memory>
#include "interfaces.h"
#include "train_manager.h"

struct TicketOrder {
    std::string orderId;
    std::string userId;
    std::string trainNo;
    std::string travelDate;
    int seatCount;
    double amount;
    std::string status;          // "PAID", "REFUNDED", "CHANGED"
    std::string changeToOrderId; // 改签后的新订单ID
};

class TicketManager {
private:
    std::unordered_map<std::string, TicketOrder> orders;
    std::shared_ptr<TrainManager> trainMgr;
    std::shared_ptr<IPaymentService> payment;
    std::shared_ptr<IMobileService> mobile;
    int orderCounter;

    std::string generateOrderId();
public:
    TicketManager(std::shared_ptr<TrainManager> tm,
        std::shared_ptr<IPaymentService> pay,
        std::shared_ptr<IMobileService> mob);

    bool buyTicket(const std::string& userId, const std::string& trainNo,
        const std::string& travelDate, int seatCount, std::string& outOrderId);
    bool refundTicket(const std::string& orderId, std::string& outMessage);
    bool changeTicket(const std::string& oldOrderId, const std::string& newTrainNo,
        const std::string& newTravelDate, std::string& outNewOrderId);
    void listUserOrders(const std::string& userId) const;
};

#endif