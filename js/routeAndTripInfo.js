// file with code for showing route/trip info below itinerary list

// route info
function showRouteInfo(routeJkey) {
  let content = `<div id="route_info"><span id="expand_route_info" onclick="expandRouteInfo(\'${routeJkey}\')">`;
  content += 'route info</span></div>';

  document.getElementById('sidebar').innerHTML += content;
}

function expandRouteInfo(routeJkey) {
  if (!routeExpanded) {
    document.getElementById('expand_route_info').style.color = '#30b566';
    loadJsonFileAsObj(`./.visualizefiles/routes/${routeJkey}.json`, (route) => {
      let content = '<br>';
      Object.keys(route).forEach((routeAttr) => {
        // sample_trip_jkeys not a gtfs field
        if (routeAttr !== 'sample_trip_jkeys') {
          content += `<br><span class="field_header">${routeAttr}</div><br>`;
          content += `<span class="field">${route[routeAttr]}</span>`;
        }
      });
  
      document.getElementById('route_info').innerHTML += content;
      routeExpanded = true;
    }, () => {
      document.getElementById('route_info').innerHTML += '<br><span class="error>Could not load route info</span>';
      routeExpanded = true;
    });
  } else {
    document.getElementById('expand_route_info').style.color = '#14446b';
    document.getElementById('route_info').innerHTML = `<span id="expand_route_info" onclick="expandRouteInfo(\'${routeJkey}\')">route info</span>`;
    routeExpanded = false;
  }
}

function clearRouteInfo() {
  routeExpanded = false;
  activeRouteInfo = null;
  try {
    document.getElementById('route_info').remove();
  } catch (err) {}
}


// trip info
function showTripInfo(tripJkey) {
  let content = `<div id="trip_info"><span id="expand_trip_info" onclick="expandTripInfo(\'${tripJkey}\')">`;
  content += 'trip info</span></div>';

  document.getElementById('sidebar').innerHTML += content;
}

function expandTripInfo(tripJkey) {
  if (!tripExpanded) {
    document.getElementById('expand_trip_info').style.color = '#30b566';

    if (cachedTripInfo[tripJkey]) {
      displayTripInfo(cachedTripInfo[tripJkey], tripJkey);
    } else {
      loadJsonFileAsObj(`./.visualizefiles/trips/${tripJkey}.json`, (trip) => {
        displayTripInfo(trip, tripJkey);
      }, () => {
        document.getElementById('trip_info').innerHTML += '<br><span class="error>Could not load trip info</span>';
        tripExpanded = true;
      });
    }
  } else {
    document.getElementById('expand_trip_info').style.color = '#14446b';
    document.getElementById('trip_info').innerHTML = `<span id="expand_trip_info" onclick="expandTripInfo(\'${tripJkey}\')">trip info</span>`;
    tripExpanded = false;
  }
}

function displayTripInfo(trip, tripJkey) {
  let content = '<br>';
  Object.keys(trip).forEach((tripAttr) => {
    // route id is redundant; timing_list, itinerary_id and departure_time not gtfs values
    if (tripAttr !== 'trip_jkey' && tripAttr != 'route_jkey' && tripAttr != 'service_jkey' && tripAttr !== 'itinerary_id' && tripAttr !== 'departure_time' && tripAttr !== 'timing_list') {
      content += `<br><span class="field_header">${tripAttr}</div><br>`;
      content += `<span class="field">${trip[tripAttr]}</span>`;
    }
  });

  document.getElementById('trip_info').innerHTML += content;
  tripExpanded = true;
}

function clearTripInfo() {
  tripExpanded = false;
  if (activeTrip) {
    document.getElementById('trip_info').remove();
  }
}
