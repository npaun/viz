#ifndef routes_loader_h
#define routes_loader_h
#include "gtfs_files.h"
#include "sjson.h"
#include "stop_times_loader.h"
#include <iostream>
#include <jsonxx.h>
#include <memory>
#include <sstream>
#include <string>
#include <sys/stat.h>
#include <unordered_map>
#include <vector>

namespace npvis {
class routes_loader {
public:
  using table_itineraries = std::vector<std::string>;

  static std::unique_ptr<table_itineraries>
  gen_itineraries(const stop_times_loader::analysis_t &analysis) {

    auto table = std::make_unique<table_itineraries>();
    table->resize(analysis.itineraries.size());

    for (const auto &[itinerary_key, itinerary] : analysis.itineraries) {
      const auto &stop_list = itinerary_key.locations;
      const auto &sample_trip = *itinerary.sample_trips.front();
      sjson::object itin_obj;

      std::stringstream itinerary_name;
      const auto &first_stop = *(stop_list.begin()->stop_ref);
      itinerary_name << first_stop.at("stop_name") << " → ";
      const auto &last_stop = *(stop_list.rbegin()->stop_ref);
      itinerary_name << last_stop.at("stop_name") << ", ";
      itinerary_name << stop_list.size() << " stops";

      itin_obj.add("itinerary_name", itinerary_name.str());
      itin_obj.add_jkey("shape_jkey", sample_trip.at("shape_id"));

      std::vector<std::tuple<std::string, double, double>> stop_list_obj;
      stop_list_obj.reserve(stop_list.size());

      for (const auto &[stop_seq, stop_ref] : stop_list) {

        stop_list_obj.emplace_back(stop_ref->at("stop_id"),
                                   std::stod(stop_ref->at("stop_lat")),
                                   std::stod(stop_ref->at("stop_lon")));
      }

      itin_obj.add("stop_list", stop_list_obj);

      table->operator[](itinerary.itinerary_id) = itin_obj.str();
    }

    std::cout << "T\tready to serve /itineraries from memory" << std::endl;
    return table;
  }

  static void gen_routes(const std::string &out_dir,
                         const stop_times_loader::analysis_t &analysis,
                         const gtfs::routes &routes_csv) {
    std::unordered_map<std::string, std::vector<gtfs::row_id>>
        route_samples_all_itineraries;
    for (const auto &[_, itinerary] : analysis.itineraries) {
      const auto &sample_trip = *itinerary.sample_trips.front();
      auto &sample_dest =
          route_samples_all_itineraries[sample_trip.at("route_id")];
      for (const auto &extra_sample : itinerary.sample_trips) {
        sample_dest.push_back(extra_sample->id);
      }
    }

    for (const auto &[route_id, sample_trips] : route_samples_all_itineraries) {
      const auto &route = routes_csv.at(route_id);
      auto route_json = gtfs::routes::toJson(route);
      route_json.add_str("sample_trip_jkeys", sample_trips);

      std::ofstream route_file(out_dir + "/routes/" +
                                   sjson::id_tojkey(route_id) + ".json",
                               std::ios::binary);
      route_file << route_json.str();
    }

    std::cout << "T\twrote /routes to disk" << std::endl;
  }
};
} // namespace npvis
#endif
