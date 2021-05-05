#ifndef gtfs_files_h
#define gtfs_files_h
#include "sjson.h"
#include <cstddef>
#include <cstring>
#include <csvmonkey.hpp>
#include <openssl/md5.h>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

using namespace csvmonkey;

namespace npvis::gtfs {

using cell = CsvCell *;
using fields = std::vector<FieldPair>;

const unsigned char utf8_bom[] = {0xef, 0xbb, 0xbf};

void eat_bom(MappedFileCursor &cursor) {
  if (std::memcmp(cursor.buf(), utf8_bom, 3) == 0) {
    std::cout << "This CSV has a BOM for some reason. Ignored." << std::endl;
    cursor.consume(3);
  }
}

struct stop_times {
  cell stop_id, trip_id, stop_sequence, departure_time, arrival_time;
  MappedFileCursor cursor;
  CsvReader<MappedFileCursor> reader;

  stop_times(const std::string &directory) : reader(cursor, ',', '"', 0, true) {
    auto path = directory + "/" + get_name();
    cursor.open(path.c_str());
    eat_bom(cursor);
    reader.read_row();
    reader.extract_fields(get_fields());
  }

  bool read() { return reader.read_row(); }

  fields get_fields() {
    return {{"stop_id", &stop_id},
            {"trip_id", &trip_id},
            {"stop_sequence", &stop_sequence},
            {"departure_time", &departure_time},
            {"arrival_time", &arrival_time}};
  }

  std::string get_name() { return "stop_times.txt"; }
};

using primary_key = std::string;
using row_id = std::size_t;
struct entry : public std::unordered_map<std::string, std::string> {
  row_id id;
  entry(row_id id) : id(id) {}
};

const char *bad_chars = " \t";

/** If we need to fix every cell read, we'll need to improve this function
 * For now, it's a complete noop
 */
#define strip(s) s

template <typename Impl>
struct gtfs_mapper : public std::unordered_map<primary_key, entry> {
  MappedFileCursor cursor;
  CsvReader<MappedFileCursor> reader;

  CsvCell *pkey_cell;
  std::vector<std::pair<std::string, CsvCell *>> cells;

  CsvCell null_cell;

  gtfs_mapper(const std::string &directory)
      : reader(cursor, ',', '"', 0, true), null_cell{"", 0, 0, '"', false} {
    auto path = directory + "/" + impl().name();
    cursor.open(path.c_str());
    eat_bom(cursor);

    reader.read_row();
    auto pkey = impl().primary_key();

    reader.extract_fields({{pkey.c_str(), &pkey_cell}});

    auto &row = reader.row();
    auto field_set = impl().fields();
    cells.reserve(row.count);
    for (std::size_t i = 0; i < row.count; i++) {
      auto column_name = strip(row.cells[i].as_str());
      if (field_set.erase(column_name)) {
        cells.push_back({column_name, &row.cells[i]});
      }
    }

    // Now we have some missing fields
    for (const auto &missing_field : field_set) {
      std::cout << "Adding empty field " << missing_field << std::endl;
      cells.push_back({missing_field, &null_cell});
    }

    std::size_t i = 0;
    while (reader.read_row()) {
      auto [it, _] = try_emplace(strip(pkey_cell->as_str()), i);
      auto &dataMap = it->second;
      dataMap.reserve(cells.size());
      for (const auto &[cell_name, cell_ptr] : cells) {
        dataMap.try_emplace(cell_name, strip(cell_ptr->as_str()));
      }

      i++;
    }

    std::cout << "T\tloaded " << impl().name() << std::endl;
  }

  static sjson::object toJson(const entry &row) {
    sjson::object obj;
    obj.extend(row);
    return obj;
  }

  Impl &impl() { return reinterpret_cast<Impl &>(*this); }
};

struct trips : gtfs_mapper<trips> {
  using gtfs_mapper<trips>::gtfs_mapper;

  std::string name() { return "trips.txt"; }

  std::string primary_key() { return "trip_id"; }

  std::unordered_set<std::string> fields() {
    return {"trip_id",    "route_id",        "block_id",     "shape_id",
            "service_id", "trip_short_name", "trip_headsign"};
  }
};

struct routes : gtfs_mapper<routes> {
  using gtfs_mapper<routes>::gtfs_mapper;

  std::string name() { return "routes.txt"; }

  std::string primary_key() { return "route_id"; }

  std::unordered_set<std::string> fields() {
    return {"route_id", "route_type", "route_short_name", "route_long_name"};
  }
};

struct stops : gtfs_mapper<stops> {
  using gtfs_mapper<stops>::gtfs_mapper;

  std::string name() { return "stops.txt"; }

  std::string primary_key() { return "stop_id"; }

  std::unordered_set<std::string> fields() {
    return {"stop_id", "location_type", "stop_name", "stop_lat", "stop_lon"};
  }
};
} // namespace npvis::gtfs

#endif
