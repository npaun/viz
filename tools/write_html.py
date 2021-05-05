import json

html_start = """
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">

  <head>
    <meta charset="UTF-8">
    <!--mapbox stuff-->
    <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
    <script src="https://api.mapbox.com/mapbox-gl-js/v1.12.0/mapbox-gl.js"></script>
    <link href="https://api.mapbox.com/mapbox-gl-js/v1.12.0/mapbox-gl.css" rel="stylesheet" />

    <link rel="stylesheet" type="text/css" href="css/visualizer.css">

    <title>visualizer</title>
  </head>

  <body>

    <div id='map'>
    </div>

    <div id='sidebar'>
      <div id='date_finder'>
        <div class='header' id="date_header">select a date (default today)</div>
        <input type="text" id="date_search" placeholder="enter YYYYMMDD only"><span id="date_entered" onclick="inputClicked('date_search', 'date_entered', 'datebutton')"></span><button type="button" id="datebutton" onclick="onEnterDate()">enter</button>
      </div>

      <div id='time_finder'>
        <div class='header'>select a time (default 08:00)</div>
        <input type="text" id="time_search" placeholder="enter HH:MM only"><span id="time_entered" onclick="inputClicked('time_search', 'time_entered', 'timebutton')"></span><button type="button" id="timebutton" onclick="onEnterTime()">enter</button>
      </div>

      <div id='trip_finder'>
        <div class='header'>visualize a trip</div>
        <input type="text" id="trip_search" placeholder="enter trip id"><span id="trip_entered" onclick="inputClicked('trip_search', 'trip_entered', 'tripbutton')"></span><button type="button" id="tripbutton" onclick="onEnterTripId()">enter</button>
      </div>

      <div id='browse_routes'>
        <div class='header'>browse routes</div>
        <table id="routes_table">
"""

html_end = """
        </table>
        <table id="itins_table"></table>
      </div>
    </div>
    <script src="js/config.js"></script>
    <script src="js/tools.js"></script>
    <script src="js/eventListeners.js"></script>
    <script src="js/routeAndTripInfo.js"></script>
    <script src="js/visualizer.js"></script>
  </body>

</html>
"""

def write_html(routes_obj):
    def sort_function(route_item):
        return route_item[1]['route_short_name']

    html_middle = ''
    routes_list = []
    for item in routes_obj.items():
        routes_list.append(item)

    routes_list.sort(key=sort_function)
    for item in routes_list:
        route_long_name = item[1]['route_long_name']
        route_short_name = item[1]['route_short_name']
        route_jkey = item[0]

        if len(route_long_name) > 50:
            route_long_name = route_long_name[:50] + '...'
        if len(route_short_name) > 50:
            route_short_name = route_short_name[:50] + '...'

        html_middle += '\n<tr style="padding-top: 10px;" onclick="routeClicked('
        html_middle += "'" + route_jkey + "', '" + route_short_name.replace('\'', '\\\'') + "'" + ')"><td class="route_short_name">'
        html_middle += route_short_name
        html_middle += '</td><td class="route_long_name">'
        html_middle += route_long_name
        html_middle += '</td></tr>'
    html_middle += '\n'

    with open('.visualizefiles/visualizer.html', 'w') as htmlfile:
        htmlfile.write(html_start)
        htmlfile.write(html_middle)
        htmlfile.write(html_end)
