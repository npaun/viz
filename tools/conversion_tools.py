import json
import geojson
import os.path
import csv
import datetime
import re
import hashlib
from . import write_html

# desired output
# /itineraries:
#   object (key=route_jkey_itin_id):
#     shape_key
#     list of stop ids with time offset after each one
# /trips
#   one file per trip
#    object (key=trip_jkey):
#      start_time
#      itinerary id
#      headsign, short_name, other unrequired fields
#   AND
#      one file: trip_jkey_by_trip_id
# /trips_by_route_by_hour
#   one file per service_jkey_route_jkey
#   object (key=service_jkey_route_jkey):
#     object (key=hour, where the hour is the hour in which the trip starts):
#       array of trip jkeys in ascending order of start time
# /service_jkeys_by_date
#   one file
#   object (key=date):
#     active service_jkeys on this date
# /routes
#   one file per route_jkey
# /stops
#   one file
# /shapes
#   one file per shape, named by shape_jkey

itin_separator = "_jitin_"


def convert_calendars(calendar_path, calendar_dates_path, out_dir):
    use_calendar = os.path.isfile(calendar_path)
    use_cal_dates = os.path.isfile(calendar_dates_path)
    if not (use_cal_dates or use_calendar):
        print("No calendar.txt or calendar_dates.txt file found. Will not visualize.")
        exit(1)

    service_jkeys_by_date = {}
    if use_calendar:
        with open(calendar_path, "r", encoding="utf-8-sig") as calendar:
            calendar_reader = csv.DictReader(calendar, skipinitialspace=True)

            for line in calendar_reader:
                start_date, end_date, service_jkey = "", "", ""
                date_array = ["", "", "", "", "", "", ""]
                try:
                    start_date = line["start_date"]
                    end_date = line["end_date"]
                    service_id = line["service_id"]
                    service_jkey = hashlib.md5(service_id.encode()).hexdigest()
                    date_array[0] = line["monday"]
                    date_array[1] = line["tuesday"]
                    date_array[2] = line["wednesday"]
                    date_array[3] = line["thursday"]
                    date_array[4] = line["friday"]
                    date_array[5] = line["saturday"]
                    date_array[6] = line["sunday"]
                except:
                    print("Required field in calendar.txt not found. Will not visualize.")
                    exit(1)

                start_year, start_month, start_day, end_year, end_month, end_day = 0, 0, 0, 0, 0, 0
                try:
                    start_year = int(start_date[:4])
                    start_month = int(start_date[4:6])
                    start_day = int(start_date[6:])
                    end_year = int(end_date[:4])
                    end_month = int(end_date[4:6])
                    end_day = int(end_date[6:])
                except:
                    print("Date in calendar.txt in wrong format. Will not visualize.")
                    exit(1)

                start = datetime.datetime(start_year, start_month, start_day)
                end = datetime.datetime(end_year, end_month, end_day)

                while start <= end:
                    print_date = start.strftime("%Y%m%d")
                    date_day = start.weekday()
                    if not print_date in service_jkeys_by_date:
                        service_jkeys_by_date[print_date] = []
                    if date_array[date_day] == "1":
                        service_jkeys_by_date[print_date].append(service_jkey)

                    start += datetime.timedelta(days=1)

    if use_cal_dates:
        with open(calendar_dates_path, "r", encoding="utf-8-sig") as cal_dates:
            dates_reader = csv.DictReader(cal_dates, skipinitialspace=True)

            for line in dates_reader:
                service_jkey, date, exception_type = "", "", ""
                try:
                    service_id = line["service_id"]
                    service_jkey = hashlib.md5(service_id.encode()).hexdigest()
                    date = line["date"]
                    exception_type = line["exception_type"]
                except:
                    print("Required value in calendar_dates.txt missing. Will not visualize.")
                    exit(1)

                if exception_type == "1":
                    if not date in service_jkeys_by_date:
                        service_jkeys_by_date[date] = []
                    service_jkeys_by_date[date].append(service_jkey)

                if exception_type == "2":
                    try:
                        service_jkeys_by_date[date].remove(service_jkey)
                    except:
                        continue

    return service_jkeys_by_date


def convert_routes(routes_path, out_dir):
    if not os.path.isfile(routes_path):
        print("No routes.txt file found. Will not visualize.")
        exit(1)

    routes_obj = {}
    with open(routes_path, "r", encoding="utf-8-sig") as routes:
        routes_reader = csv.DictReader(routes, skipinitialspace=True)

        for line in routes_reader:
            route_id = ""
            route_jkey = ""
            try:
                route_id = line["route_id"]
                route_jkey = hashlib.md5(route_id.encode()).hexdigest()
                routes_obj[route_jkey] = {}
                routes_obj[route_jkey]["route_type"] = line["route_type"]
                routes_obj[route_jkey]["route_id"] = route_id
            except:
                print("route_id or route_type missing. Will not visualize.")
                exit(1)

            name_found = False
            for attr in ["route_short_name", "route_long_name"]:
                try:
                    routes_obj[route_jkey][attr] = line[attr]
                    name_found = True
                except:
                    continue

            if not name_found:
                print("Both route_short_name and route_long_name missing. Will not visualize.")
                exit(1)

    write_html.write_html(routes_obj)
    return routes_obj


def convert_shapes(shapes_path, out_dir):
    def sort_function(shape_item):
        return shape_item["shape_seq"]

    if not os.path.isfile(shapes_path):
        print("No shapes.txt file found. Will not visualize shapes.")
        return

    shapes_obj = {}

    with open(shapes_path, "r", encoding="utf-8-sig") as shapes:
        shapes_reader = csv.DictReader(shapes, skipinitialspace=True)

        for line in shapes_reader:
            shape_jkey = ""
            shape_lon, shape_lat = 0.0, 0.0
            shape_seq = 0
            try:
                shape_id = line["shape_id"]
                shape_jkey = hashlib.md5(shape_id.encode()).hexdigest()
                shape_lon = float(line["shape_pt_lon"])
                shape_lat = float(line["shape_pt_lat"])
                shape_seq = int(line["shape_pt_sequence"])
            except:
                print("Error: could not read shapes.txt. Shapes file has invalid fields or values")
                exit(1)

            if not shape_jkey in shapes_obj:
                shapes_obj[shape_jkey] = []

            shapes_obj[shape_jkey].append(
                {"shape_lon": shape_lon, "shape_lat": shape_lat, "shape_seq": shape_seq}
            )

    for key in shapes_obj:
        line_coords = []
        shapes_obj[key].sort(key=sort_function)
        for coords in shapes_obj[key]:
            line_coords.append((coords["shape_lon"], coords["shape_lat"]))

        geojson_line = geojson.LineString(line_coords)
        geojson_feature = geojson.Feature(geometry=geojson_line)

        out_path = os.path.join(out_dir, key + ".json")
        with open(out_path, "w") as out:
            geojson.dump(geojson_feature, out)


def convert_stops(stops_path, stops_dir):
    stops_obj = {}
    with open(stops_path, "r", encoding="utf-8-sig") as stops:
        stops_reader = csv.DictReader(stops, skipinitialspace=True)

        for line in stops_reader:
            location_type = ""
            try:
                location_type = line["location_type"]
            except:
                location_type = "0"

            if location_type == "" or location_type == "0":
                try:
                    stop_id = line["stop_id"]
                    stops_obj[stop_id] = {}
                    stops_obj[stop_id]["stop_lat"] = float(line["stop_lat"])
                    stops_obj[stop_id]["stop_lon"] = float(line["stop_lon"])
                    stops_obj[stop_id]["stop_name"] = line["stop_name"]
                except:
                    print(
                        "Missing or badly formatted required value in stops.txt. Will not visualize."
                    )
                    exit(1)

    out_path = os.path.join(stops_dir, "stops.json")
    with open(out_path, "w") as out:
        json.dump(stops_obj, out)

    return stops_obj


def read_trips(trips_path, trips_dir, routes_obj):
    trips_obj = {}
    trip_jkey_by_trip_id = {}

    with open(trips_path, "r", encoding="utf-8-sig") as trips:
        trips_reader = csv.DictReader(trips, skipinitialspace=True)

        trip_attributes = [
            "trip_headsign",
            "trip_direction_headsign",
            "trip_merged_headsign",
            "trip_short_name",
            "shape_id",
            "block_id",
            "direction_id",
            "trip_direction_id",
            "trip_branch_code",
        ]
        for line in trips_reader:
            trip_id, route_jkey, service_jkey, trip_jkey = "", "", "", ""
            try:
                trip_id = line["trip_id"]
                trip_jkey = hashlib.md5(trip_id.encode()).hexdigest()
                trip_jkey_by_trip_id[trip_id] = trip_jkey
                route_jkey = hashlib.md5(line["route_id"].encode()).hexdigest()
                service_jkey = hashlib.md5(line["service_id"].encode()).hexdigest()
            except:
                print("Missing trip_id or route_id in trips.txt. Unable to visualize")
                print(line)
                print(line["trip_id"])
                print(line["route_id"])
                print(line["service_id"])
                exit(1)

            if route_jkey in routes_obj:
                trips_obj[trip_jkey] = {
                    "route_jkey": route_jkey,
                    "service_jkey": service_jkey,
                    "trip_id": trip_id,
                    "trip_jkey": trip_jkey,
                }
                for attr in trip_attributes:
                    try:
                        trips_obj[trip_jkey][attr] = line[attr]
                    except:
                        continue

    out_path = os.path.join(trips_dir, "trip_jkey_by_trip_id.js")
    with open(out_path, "w") as out:
        out_string = "const tripJkeyByTripId = " + json.dumps(trip_jkey_by_trip_id) + ";"
        out.write(out_string)

    return [trips_obj, trip_jkey_by_trip_id]


def read_stop_times(stop_times_path, trips_obj, stops_obj):
    with open(stop_times_path, "r", encoding="utf-8-sig") as stop_times:
        stop_times_reader = csv.DictReader(stop_times, skipinitialspace=True)

        stop_time_attributes = [
            "stop_headsign",
            "stop_direction_headsign",
            "stop_merged_headsign",
            "stop_direction_id",
        ]
        for line in stop_times_reader:
            stop_time_obj = {}
            trip_jkey = ""
            try:
                trip_id = line["trip_id"]
                trip_jkey = hashlib.md5(trip_id.encode()).hexdigest()
                stop_time_obj["arrival_time"] = line["arrival_time"]
                stop_time_obj["departure_time"] = line["departure_time"]
                stop_time_obj["stop_id"] = line["stop_id"]
                stop_time_obj["stop_sequence"] = int(line["stop_sequence"])
            except:
                print("Missing required attribute in stop_times.txt. Unable to visualize.")
                exit(1)

            for attr in stop_time_attributes:
                try:
                    stop_time_obj[attr] = line[attr]
                except:
                    continue

            if not trip_jkey in trips_obj:
                # print("trip_id in stop_times not found in trips.txt. Will not visualize associated trip_id.")
                continue

            if not stop_time_obj["stop_id"] in stops_obj:
                # print("stop_id in stop_times not found in stops.txt. Will not visualize associated trip_id.")
                continue

            stop_time_obj["stop_lat"] = stops_obj[stop_time_obj["stop_id"]]["stop_lat"]
            stop_time_obj["stop_lon"] = stops_obj[stop_time_obj["stop_id"]]["stop_lon"]

            if not "stop_times" in trips_obj[trip_jkey]:
                trips_obj[trip_jkey]["stop_times"] = []
            trips_obj[trip_jkey]["stop_times"].append(stop_time_obj)


def process_trips(trips_obj, stops_obj):
    def sort_function(stop_time):
        return stop_time["stop_sequence"]

    itin_obj = {}
    trips_hour_obj = {}
    trip_jkeys_to_delete = []
    itins_with_sample_trips_by_route = {}
    for trip_jkey in trips_obj:
        gtfs_time_regex = r"^(\d?\d):(\d\d):(\d\d)$"

        if not "stop_times" in trips_obj[trip_jkey]:
            trip_jkeys_to_delete.append(trip_jkey)
            continue

        trips_obj[trip_jkey]["stop_times"].sort(key=sort_function)

        first_stop_time = trips_obj[trip_jkey]["stop_times"][0]["departure_time"]
        stop_time_length = len(trips_obj[trip_jkey]["stop_times"])
        last_stop_time = trips_obj[trip_jkey]["stop_times"][stop_time_length - 1]["arrival_time"]

        if not (
            re.match(gtfs_time_regex, first_stop_time)
            and re.match(gtfs_time_regex, last_stop_time)
        ):
            print("Invalid stop time format in stop_times.txt. Unable to visualize.")
            print(first_stop_time)
            exit(1)

        trips_obj[trip_jkey]["departure_time"] = first_stop_time

        departure_hour = int(first_stop_time.split(":")[0])
        route_jkey = trips_obj[trip_jkey]["route_jkey"]
        service_jkey = trips_obj[trip_jkey]["service_jkey"]
        key = route_jkey + "_" + service_jkey

        if not key in trips_hour_obj:
            trips_hour_obj[key] = {}
        if not departure_hour in trips_hour_obj[key]:
            trips_hour_obj[key][departure_hour] = []
        trips_hour_obj[key][departure_hour].append(trip_jkey)

        stop_list = []
        stop_list_hashable = []
        timing_list = []
        time_offset = 0  # in seconds
        last_time = None
        for stop_time in trips_obj[trip_jkey]["stop_times"]:
            this_time = ""
            if stop_time["arrival_time"]:
                this_time = stop_time["arrival_time"]
            elif stop_time["departure_time"]:
                this_time = stop_time["departure_time"]

            if this_time:
                try:
                    time_matched = re.match(gtfs_time_regex, this_time)
                    hh, mm, ss = (
                        int(time_matched.group(1)),
                        int(time_matched.group(2)),
                        int(time_matched.group(3)),
                    )
                    this_time = datetime.timedelta(hours=hh, minutes=mm, seconds=ss)
                except:
                    print(
                        "Invalid stop time format in stop_times.txt. Unable to visualize."
                    )
                    exit(1)
                if last_time:
                    time_offset += int((this_time - last_time).total_seconds())

            stop_id = stop_time["stop_id"]
            tuple_to_append = (
                stop_id,
                stops_obj[stop_id]["stop_lat"],
                stops_obj[stop_id]["stop_lon"],
            )
            tuple_to_hash = tuple(map(lambda x: str(x), tuple_to_append))
            stop_list.append(tuple_to_append)
            stop_list_hashable.append("___".join(tuple_to_hash))
            timing_list.append(time_offset)
            if this_time:
                last_time = this_time

        stop_list_hash = hashlib.md5("-".join(tuple(stop_list_hashable)).encode()).hexdigest()
        itinerary_id = trips_obj[trip_jkey]["route_jkey"] + itin_separator + stop_list_hash
        trips_obj[trip_jkey]["itinerary_id"] = itinerary_id
        trips_obj[trip_jkey]["timing_list"] = timing_list

        if not itinerary_id in itin_obj:
            first_stop_name = stops_obj[stop_list[0][0]]["stop_name"]
            last_stop_name = stops_obj[stop_list[len(stop_list) - 1][0]]["stop_name"]
            itin_name = (
                first_stop_name
                + " → "
                + last_stop_name
                + ", "
                + str(len(stop_list))
                + " stops"
            )
            itin_obj[itinerary_id] = {}
            itin_obj[itinerary_id]["stop_list"] = stop_list
            itin_obj[itinerary_id]["shape_jkey"] = ""
            itin_obj[itinerary_id]["itinerary_name"] = itin_name
            if not trips_obj[trip_jkey]["route_jkey"] in itins_with_sample_trips_by_route:
                itins_with_sample_trips_by_route[trips_obj[trip_jkey]["route_jkey"]] = {}
            itins_with_sample_trips_by_route[trips_obj[trip_jkey]["route_jkey"]][itinerary_id] = []
        if "shape_id" in trips_obj[trip_jkey]:
            if not trips_obj[trip_jkey]["shape_id"] == "":
                itin_obj[itinerary_id]["shape_jkey"] = hashlib.md5(trips_obj[trip_jkey]["shape_id"].encode()).hexdigest()
        if len(itins_with_sample_trips_by_route[trips_obj[trip_jkey]["route_jkey"]][itinerary_id]) < 3:
            itins_with_sample_trips_by_route[trips_obj[trip_jkey]["route_jkey"]][itinerary_id].append(trip_jkey)

        del trips_obj[trip_jkey]["stop_times"]

    for trip_jkey_to_delete in trip_jkeys_to_delete:
        del trips_obj[trip_jkey_to_delete]

    return [itin_obj, trips_hour_obj, itins_with_sample_trips_by_route]


def convert_trips(stops_path, trips_path, stop_times_path, stops_dir, trips_dir, itin_dir, trips_hour_dir, routes_dir):
    if not os.path.isfile(trips_path):
        print("No trips.txt file found. Will not visualize.")
        exit(1)

    if not os.path.isfile(stop_times_path):
        print("No stop_times.txt file found. Will not visualize.")
        exit(1)

    if not os.path.isfile(stops_path):
        print("No stops.txt file found. Will not visualize.")
        exit(1)

    stops_obj = convert_stops(stops_path, stops_dir)
