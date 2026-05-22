#include "train_manager.h"
#include <algorithm>

TrainManager::TrainManager() {
    // 初始化默认车次
    trains["G101"] = { "G101", "北京", "上海", "08:00", "12:00", 553.0, 100, 100 };
    trains["D202"] = { "D202", "北京", "广州", "10:00", "18:00", 862.0, 80, 80 };
    trains["K301"] = { "K301", "上海", "成都", "15:30", "次日12:30", 278.5, 120, 120 };
}

bool TrainManager::addTrain(const Train& train) {
    if (trains.find(train.trainNo) != trains.end()) return false;
    trains[train.trainNo] = train;
    return true;
}

bool TrainManager::updateTrain(const std::string& trainNo, double newPrice, int newTotalSeats) {
    auto it = trains.find(trainNo);
    if (it == trains.end()) return false;
    it->second.price = newPrice;
    int delta = newTotalSeats - it->second.totalSeats;
    it->second.totalSeats = newTotalSeats;
    it->second.availableSeats += delta;
    if (it->second.availableSeats < 0) it->second.availableSeats = 0;
    return true;
}

std::vector<Train> TrainManager::searchTrains(const std::string& from, const std::string& to) const {
    std::vector<Train> result;
    for (const auto& pair : trains) {
        const auto& t = pair.second;
        if (t.departure == from && t.destination == to) {
            result.push_back(t);
        }
    }
    return result;
}

Train* TrainManager::getTrain(const std::string& trainNo) {
    auto it = trains.find(trainNo);
    if (it != trains.end()) return &it->second;
    return nullptr;
}

bool TrainManager::deductSeats(const std::string& trainNo, int count) {
    Train* train = getTrain(trainNo);
    if (!train || train->availableSeats < count) return false;
    train->availableSeats -= count;
    return true;
}

bool TrainManager::restoreSeats(const std::string& trainNo, int count) {
    Train* train = getTrain(trainNo);
    if (!train) return false;
    train->availableSeats += count;
    if (train->availableSeats > train->totalSeats) train->availableSeats = train->totalSeats;
    return true;
}