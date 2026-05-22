#ifndef TRAIN_MANAGER_H
#define TRAIN_MANAGER_H

#include <string>
#include <vector>
#include <unordered_map>

struct Train {
    std::string trainNo;
    std::string departure;
    std::string destination;
    std::string depTime;
    std::string arrTime;
    double price;
    int totalSeats;
    int availableSeats;
};

class TrainManager {
private:
    std::unordered_map<std::string, Train> trains; // trainNo -> Train
public:
    TrainManager();  // 初始化默认车次
    bool addTrain(const Train& train);
    bool updateTrain(const std::string& trainNo, double newPrice, int newTotalSeats);
    std::vector<Train> searchTrains(const std::string& from, const std::string& to) const;
    Train* getTrain(const std::string& trainNo);
    bool deductSeats(const std::string& trainNo, int count);
    bool restoreSeats(const std::string& trainNo, int count);
};

#endif