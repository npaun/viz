#!/usr/bin/env python3
import os
import signal
import sys
import shutil
import http.server
import socketserver
from tools.conversion_tools import convert_calendars, convert_routes, convert_shapes, convert_trips
import ctypes
import datetime
from flask import Flask, send_from_directory, Response, send_file
import threading, webbrowser


libvis = ctypes.CDLL('./backend/lib/libvis.so')
libvis.serve_trip.restype = ctypes.c_char_p
libvis.serve_itinerary.restype = ctypes.c_char_p
libvis.serve_trip_index.restype = ctypes.c_char_p
libvis.serve_trips_by_hour.restype = ctypes.c_char_p
now = datetime.datetime.utcnow()
last_modified = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
expires = (now + datetime.timedelta(hours=1)).strftime('%a, %d %b %Y %H:%M:%S GMT')

app = Flask(__name__)

@app.route('/')
def home():
    return send_file('.visualizefiles/visualizer.html')

@app.after_request
def enable_caching(resp):
    resp.headers['Cache-Control'] = 'public; max-age=3600'
    resp.headers['Last-Modified'] = last_modified
    resp.headers['Expires'] = expires
    return resp

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('', path)

@app.route('/.visualizefiles/trips/<int:trip_id>.json')
def serve_trip(trip_id):
    return Response(libvis.serve_trip(trip_id), mimetype='application/json')

@app.route('/.visualizefiles/itineraries/<ignore>/itin_<int:itin_id>.json')
def serve_itinerary(ignore, itin_id):
    return Response(libvis.serve_itinerary(itin_id), mimetype='application/json')

@app.route('/.visualizefiles/trip_index/<trip_id>.json')
def serve_trip_index(trip_id):
    return Response(libvis.serve_trip_index(trip_id.encode()), mimetype='application/json')

@app.route('/.visualizefiles/trips_by_date/<date>/<route_id>.json')
def serve_trips_by_hour(date, route_id):
    results = []
    for service_jkey in service_by_date.get(date, []):
        result = libvis.serve_trips_by_hour(route_id.encode(), service_jkey.encode())
        if result:
            results.append(result)

    return Response(b'[%b]' % b', '.join(results), mimetype='application/json')



def signal_handler(sig, frame):
    print('\n\nClosing visualizer, deleting visualizer files. Please wait a tiny bit.')
    try:
        shutil.rmtree('.visualizefiles')
    except:
        print('No previous visualized files found on close. Weird.')
    exit(0)

def cpp_backend(in_dir, out_dir):
    libvis.generate_all(in_dir.encode(), out_dir.encode())

if __name__ == "__main__":
    mapbox_secret = os.environ.get('MAPBOX_KEY', None)
    if mapbox_secret:
        with open('js/config.js', 'w') as f:
            f.write("const MAPBOX_KEY = '%s';\n" % mapbox_secret)


    signal.signal(signal.SIGINT, signal_handler)

    gtfs_dir = ''

    try:
        in_dir = sys.argv[1]
    except:
        print("Error: must specify GTFS directory as arg")
        exit(1)

    try:
        shutil.rmtree('.visualizefiles')
    except:
        print('No previous visualized files found. Generating vis files.')
    os.makedirs('.visualizefiles', exist_ok=True)

    calendar_file = os.path.join(in_dir, "calendar.txt")
    calendar_dates_file = os.path.join(in_dir, "calendar_dates.txt")
    cal_dir = os.path.join('.visualizefiles', 'service_jkeys_by_date')
    os.mkdir(cal_dir)
    service_by_date = convert_calendars(calendar_file, calendar_dates_file, cal_dir)

    routes_file = os.path.join(in_dir, "routes.txt")
    routes_dir = os.path.join('.visualizefiles', 'routes')
    os.mkdir(routes_dir)
    routes_obj = convert_routes(routes_file, routes_dir)

    shapes_file = os.path.join(in_dir, "shapes.txt")
    shapes_dir = os.path.join('.visualizefiles', 'shapes')
    os.mkdir(shapes_dir)
    convert_shapes(shapes_file, shapes_dir)

    stops_file = os.path.join(in_dir, "stops.txt")
    trips_file = os.path.join(in_dir, "trips.txt")
    stop_times_file = os.path.join(in_dir, "stop_times.txt")
    stops_dir = os.path.join('.visualizefiles', 'stops')
    trips_dir = os.path.join('.visualizefiles', 'trips')
    itin_dir = os.path.join('.visualizefiles', 'itineraries')
    trips_hour_dir = os.path.join('.visualizefiles', 'trips_by_route_by_hour')
    os.mkdir(stops_dir)
    os.mkdir(trips_dir)
    os.mkdir(itin_dir)
    os.mkdir(trips_hour_dir)
    convert_trips(stops_file, trips_file, stop_times_file, stops_dir, trips_dir, itin_dir, trips_hour_dir, routes_dir)
    cpp_backend(in_dir, '.visualizefiles')
    if len(sys.argv) > 2 and sys.argv[2] == 'bench':
        raise SystemExit

    # start server
    PORT = os.environ.get('PORT', 8000)
    url = f'http://localhost:{PORT}/'
    print(f'go to {url}')
    threading.Timer(0.1111, lambda: webbrowser.open(url)).start()
    app.run(host='0.0.0.0', port=PORT)
