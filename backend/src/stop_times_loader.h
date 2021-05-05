#ifndef stop_times_loader_h
#define stop_times_loader_h
#include "gtfs_files.h"
#include <algorithm>
#include <charconv>
#include <cstddef>
#include <iostream>
#include <jsonxx.h>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <tuple>
#include <unordered_map>
#include <utility>
#include <vector>

namespace npvis {
class stop_times_loader {
public:
  using gtfs_time_t = std::size_t;
  using trip_id_t = std::string;

private:
  using stop_id_t = std::string;
  using stop_seq_t = std::size_t;
  using stop_index_t = std::size_t;
  struct timing {
    stop_seq_t seq;
    gtfs_time_t time;
    timing(stop_seq_t seq, gtfs_time_t time) : seq(seq), time(time) {}

    bool operator<(const timing &other) const { return seq < other.seq; }
    bool operator==(const timing &other) const {
      return seq == other.seq && time == other.time;
    }
  };

  struct location {
    stop_seq_t seq;
    const gtfs::entry *stop_ref;
    location(stop_seq_t seq, const gtfs::entry *stop_ref)
        : seq(seq), stop_ref(stop_ref) {}

    bool operator<(const location &other) const {
      return std::tie(seq, stop_ref) < std::tie(other.seq, other.stop_ref);
    }
    bool operator==(const location &other) const {
      return seq == other.seq && stop_ref == other.stop_ref;
    }
  };

  struct trip {
    std::set<timing> times;
    std::set<location> locations;
    int itinerary_id = -1;
  };

  struct itinerary_key {
    gtfs::row_id route_id;
    std::set<location> locations;
    itinerary_key(gtfs::row_id route_id, const std::set<location> &locations)
        : route_id(route_id), locations(locations) {}

    bool operator<(const itinerary_key &other) const {
      return std::tie(route_id, locations) <
             std::tie(other.route_id, other.locations);
    }
    bool operator==(const itinerary_key &other) const {
      return std::tie(route_id, locations) ==
             std::tie(other.route_id, other.locations);
    }
  };

  struct itinerary {
    std::size_t itinerary_id;
    std::vector<const gtfs::entry *> sample_trips;
    itinerary(std::size_t itinerary_id) : itinerary_id(itinerary_id) {}
  };

  static gtfs_time_t parse_time(const std::string &time_str) {
    gtfs_time_t h;
    gtfs_time_t m;
    gtfs_time_t s;

    auto hmSep = time_str.find(':');
    auto msSep = time_str.find(':', hmSep + 1);

    std::from_chars(time_str.data(), time_str.data() + hmSep, h);
    std::from_chars(time_str.data() + hmSep + 1, time_str.data() + msSep, m);
    std::from_chars(time_str.data() + msSep + 1,
                    time_str.data() + time_str.size(), s);

    return 3600 * h + 60 * m + s;
  }

public:
  struct analysis_t {
    std::map<itinerary_key, itinerary> itineraries;
    std::unordered_map<const gtfs::entry *, trip> trips;
  };

  static analysis_t load(const std::string &gtfs_dir,
                         const gtfs::stops &stops_csv,
                         const gtfs::trips &trips_csv,
                         const gtfs::routes &routes_csv) {
    analysis_t analysis;

    gtfs::stop_times cells(gtfs_dir);

    while (cells.read()) {
      auto stop_id = strip(cells.stop_id->as_str());
      auto stop_it = stops_csv.find(stop_id);
      if (stop_it == stops_csv.end()) {
        continue;
      }

      auto trip_id = strip(cells.trip_id->as_str());
      auto trip_it = trips_csv.find(trip_id);
      if (trip_it == trips_csv.end()) {
        continue;
      }

      auto time = cells.arrival_time->size
                      ? parse_time(cells.arrival_time->as_str())
                      : parse_time(cells.departure_time->as_str());
      auto stop_seq = cells.stop_sequence->as_double();

      auto [trip_data, _2] = analysis.trips.try_emplace(&(trip_it->second));
      trip_data->second.times.emplace(stop_seq, time);
      trip_data->second.locations.emplace(stop_seq, &(stop_it->second));
    }

    for (auto trip_it = analysis.trips.begin(); trip_it != analysis.trips.end();
         /* noop */) {
      auto &[trip_ref, trip] = *trip_it;

      auto route_id = trip_ref->at("route_id");
      auto route_it = routes_csv.find(route_id);

      if (route_it == routes_csv.end()) {
        std::cout << "Trip " << trip_ref->at("trip_id")
                  << " refers to non-existent route " << route_id
                  << "; destroyed." << std::endl;
        trip_it = analysis.trips.erase(trip_it);
        continue;
      }

      auto [itinIt, _3] = analysis.itineraries.try_emplace(
          {route_it->second.id, trip.locations}, analysis.itineraries.size());
      trip.itinerary_id = itinIt->second.itinerary_id;

      if (itinIt->second.sample_trips.size() < 3) {
        itinIt->second.sample_trips.emplace_back(trip_ref);
      }

      ++trip_it;
    }

    std::cout << "|itineraries| = " << analysis.itineraries.size() << std::endl;
    std::cout << "|trips| = " << analysis.trips.size() << std::endl;
    return analysis;
  }
};
} // namespace npvis
#endif
