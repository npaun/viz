#include "gtfs_files.h"
#include "routes_loader.h"
#include "stop_times_loader.h"
#include "trips_loader.h"
#include <memory>

using namespace npvis;

std::unique_ptr<trips_loader::table_trips> trips;
std::unique_ptr<trips_loader::table_trip_index> trip_index;
std::unique_ptr<trips_loader::table_trips_by_hour> trips_by_hour;
std::unique_ptr<routes_loader::table_itineraries> itineraries;

extern "C" {
const char *serve_trip(int trip_id) { return trips->at(trip_id).c_str(); }

const char *serve_itinerary(int itinerary_id) {
  return itineraries->at(itinerary_id).c_str();
}

const char *serve_trip_index(const char *trip_id) {
  if (auto trip_it = trip_index->find(trip_id); trip_it != trip_index->end()) {
    return trip_it->second.c_str();
  } else {
    return "\"NOT_FOUND\"";
  }
}

const char *serve_trips_by_hour(const char *route_id, const char *service_id) {
  if (auto trips_it = trips_by_hour->find({route_id, service_id});
      trips_it != trips_by_hour->end()) {
    return trips_it->second.c_str();
  } else {
    return "";
  }
}

void generate_all(const char *gtfs_dir, const char *out_dir) {
  gtfs::stops stops_csv(gtfs_dir);
  gtfs::trips trips_csv(gtfs_dir);
  gtfs::routes routes_csv(gtfs_dir);
  auto analysis =
      stop_times_loader::load(gtfs_dir, stops_csv, trips_csv, routes_csv);

  trips = trips_loader::trip_files(analysis, trips_csv.size());
  trip_index = trips_loader::trip_index(trips_csv);
  trips_by_hour = trips_loader::trips_by_hour(analysis);

  routes_loader::gen_routes(out_dir, analysis, routes_csv);
  itineraries = routes_loader::gen_itineraries(analysis);
}
}
