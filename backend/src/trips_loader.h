#ifndef trips_loader_h
#define trips_loader_h
#include "gtfs_files.h"
#include "sjson.h"
#include "stop_times_loader.h"
#include <cstddef>
#include <iostream>
#include <jsonxx.h>
#include <memory>
#include <sstream>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace npvis {
class trips_loader {
private:
  struct pair_hash {
    template <class T1, class T2>
    std::size_t operator()(const std::pair<T1, T2> &p) const {
      auto h1 = std::hash<T1>{}(p.first);
      auto h2 = std::hash<T2>{}(p.second);

      // Mainly for demonstration purposes, i.e. works but is overly simple
      // In the real world, use sth. like boost.hash_combine
      return h1 ^ h2;
    }
  };

public:
  using table_trips = std::vector<std::string>;

  static std::unique_ptr<table_trips>
  trip_files(const stop_times_loader::analysis_t &analysis,
             std::size_t index_range) {
    auto table = std::make_unique<table_trips>();
    table->resize(index_range);

    for (const auto &[trip_ref, trip_data] : analysis.trips) {
      sjson::object trip_json;
      trip_json.extend(*trip_ref);

      auto first_departure = trip_data.times.begin()->time;
      trip_json.add("departure_time", time_tostring(first_departure));

      std::vector<int> timing_list;
      timing_list.reserve(trip_data.times.size());

      for (const auto &[stop_seq, stop_time] : trip_data.times) {
        timing_list.push_back(stop_time - first_departure);
      }

      trip_json.add("timing_list", timing_list);
      trip_json.add("itinerary_id", trip_data.itinerary_id);
      trip_json.add_jkey("route_jkey", trip_ref->at("route_id"));
      trip_json.add_jkey("shape_jkey", trip_ref->at("shape_id"));
      trip_json.add_str("trip_jkey", trip_ref->id);
      (*table)[trip_ref->id] = trip_json.str();
    }

    std::cout << "T\tready to serve /trips from memory" << std::endl;
    return table;
  }

  using table_trip_index = std::unordered_map<std::string, std::string>;

  static std::unique_ptr<table_trip_index>
  trip_index(const gtfs::trips &trips_csv) {
    auto table = std::make_unique<table_trip_index>();

    for (const auto &[trip_id, trip_entry] : trips_csv) {
      std::stringstream sstr;
      sstr << '"' << trip_entry.id << '"';
      (*table)[trip_id] = sstr.str();
    }

    std::cout << "T\tready to serve /trip_index from memory" << std::endl;
    return table;
  }

  using route_service_key = std::pair<std::string, std::string>;

  using table_trips_by_hour =
      std::unordered_map<route_service_key, std::string, pair_hash>;
  static std::unique_ptr<table_trips_by_hour>
  trips_by_hour(const stop_times_loader::analysis_t &analysis) {

    using hour_map = std::unordered_map<std::string, std::vector<std::string>>;
    std::unordered_map<route_service_key, hour_map, pair_hash> work;
    auto table = std::make_unique<table_trips_by_hour>();

    for (const auto &[trip_ref, trip] : analysis.trips) {

      route_service_key key{sjson::id_tojkey(trip_ref->at("route_id")),
                            sjson::id_tojkey(trip_ref->at("service_id"))};
      auto hour = std::to_string(trip.times.begin()->time / 3600);
      work[key][hour].push_back(std::to_string(trip_ref->id));
    }

    table->reserve(work.size());

    for (const auto &[key, hours] : work) {
      sjson::object hoursObj;
      hoursObj.extend(hours);
      (*table)[key] = hoursObj.str();
    }

    std::cout << "T\tready to serve /trips_by_route_by_hour from memory"
              << std::endl;
    return table;
  }

  static std::string time_tostring(stop_times_loader::gtfs_time_t time) {
    std::stringstream sstr;
    auto hours = time / 3600;
    auto minsec = time % 3600;
    auto mins = minsec / 60;
    auto sec = minsec % 60;

    sstr << std::setfill('0') << std::setw(2) << hours << ":"
         << std::setfill('0') << std::setw(2) << mins << ":"
         << std::setfill('0') << std::setw(2) << sec;

    return sstr.str();
  }
};
} // namespace npvis
#endif
