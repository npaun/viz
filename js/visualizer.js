// main

const cacheId = parseInt(Math.random() * 1000000).toString();

// state trackers
let shapeShown = false; // whether or not a shape is drawn on the map
let stopsShown = false; // whether or not there are stops drawn on the map
let timePopups = []; // array of mapbox popups showing times at each stop
let activeTrip = ''; // the trip currently displayed on the map
let routeExpanded = false; // whether or not the route info panel is expanded
let tripExpanded = false; // whether or not the trip info panel is expanded
let selectedDate = ''; // date inputted by user
let selectedTime = ''; // time inputted by user
let cachedTripInfo = {}; // information about trips that have / are been / being displayed
let activeRouteInfo; // information about the route currently selected

addInputEventListeners(); // initialize event listeners

// initialize map
mapboxgl.accessToken = MAPBOX_KEY;
const map = new mapboxgl.Map({
  container: 'map', // container id
  style: 'mapbox://styles/mapbox/dark-v10', // Transit-streets
  zoom: 2, // starting zoom
});

// add the stop image for when stops get displayed
map.on('load', function() {
  map.loadImage('./files/img/stop-50.png', function(error, image) {
    if (error) throw error;
    map.addImage('custom-marker', image);
  });
});


// main functions


// called when user specifies a trip id to show through the trip id input
function showTrip(tripJkey) {
  loadJsonFileAsObj(`./.visualizefiles/trips/${tripJkey}.json`, (trip) => {
    cachedTripInfo[tripJkey] = trip;
    const itineraryId = trip['itinerary_id'];
    const routeJkey = trip['route_jkey'];
    displayItineraryWithDepTime(itineraryId, routeJkey, tripJkey);
  }, () => {
    document.getElementById('trip_finder').innerHTML += '<div id="trip_error" class="error">Could not load trip.</div>';
    setTimeout(() => {
      document.getElementById('trip_error').remove();
    }, 1000);
  });
}

// when a route is clicked, displays the itineraries of that route based on date and time entered
function routeClicked(routeJkey, routeShortName) {
  document.getElementById('routes_table').style.display = 'none';
  activeRouteInfo = { routeJkey, routeShortName };

  // add the header for the route, containing a back button to all routes and the route short name
  let tableElement = '<tr><td class="table_header"> <span class="back_button" onclick="clearRouteAndShowRouteTable()">←</span>'
  tableElement += `&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;route ${routeShortName}</td></tr>`;
  document.getElementById('itins_table').innerHTML = tableElement;
  document.getElementById('itins_table').style.display = 'block';

  addInputEventListeners();

  let dateToUse = '';
  let timeToUse = '';

  // if both date and time are unspecified or invalid, give sample trips for all itineraries of a route
  if (!/\d{8}/.test(selectedDate) && !/\d\d:\d\d/i.test(selectedTime)) {
    loadAllRouteItins(routeJkey);
  } else { // otherwise, use specified date and/or time, and use default values if one is unspecified or invalid
    if (/\d{8}/.test(selectedDate)) {
      dateToUse = selectedDate;
    } else {
      const today = new Date();
      const dd = String(today.getDate()).padStart(2, '0');
      const mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
      const yyyy = today.getFullYear();
      dateToUse = `${yyyy}${mm}${dd}`;
    }
    if (/\d\d:\d\d/i.test(selectedTime)) {
      timeToUse = selectedTime;
    } else {
      timeToUse = '08:00';
    }

    getAllTripsAtTime(routeJkey, dateToUse, timeToUse);
  }

  showRouteInfo(routeJkey);
}

// clear all elements possibly added when route was clicked
function clearRoute() {
  clearMap();
  clearRouteInfo();
  clearTripInfo();
  activeTrip = '';
  document.getElementById('itins_table').style.display = 'none';
}

function clearRouteAndShowRouteTable() {
  clearRoute();
  document.getElementById('routes_table').style.display = 'block';
}

// gets the sample trip ids for each itinerary of a route and displays them
function loadAllRouteItins(routeJkey) {
  loadJsonFileAsObj(`./.visualizefiles/routes/${routeJkey}.json`, (route) => {
    groupTripsByItineraryAndDisplay(route['sample_trip_jkeys'], routeJkey);
  }, () => {
    console.log('failed to load sample trip jkeys because route is not right');
  });
}

// gets the first three trips of each itinerary active at a spcific time and date
function getAllTripsAtTime(routeJkey, dateToUse, timeToUse) {
  let trips = [];
  let processed = 0;
  loadJsonFileAsObj(`./.visualizefiles/trips_by_date/${dateToUse}/${routeJkey}.json`, (tripsByHourByService) => {
    if (tripsByHourByService.length < 1) {
      document.getElementById('itins_table').innerHTML +=
        '<tr><td>No itineraries found for this route at this time.</td></tr>';
      return;
    }
    tripsByHourByService.forEach((tripsByHour) => {
      const hour = parseInt(timeToUse.slice(0, -3));
      if (tripsByHour[hour]) {
        trips = trips.concat(tripsByHour[hour]);
      }
      processed += 1;
      if (processed === tripsByHourByService.length) {
        groupTripsByItineraryAndDisplay(trips, routeJkey);
      }
    });
    }, () => {
      console.log(`No trips found for route ${routeJkey} on day ${dateToUse}.`);
    });
}

// given a list of trips, groups trips by itinerary (max 3 per itinerary) to then display them
function groupTripsByItineraryAndDisplay(trips, routeJkey) {
  if (trips.length === 0) {
    document.getElementById('itins_table').innerHTML +=
      '<tr><td>No itineraries found for this route at this time.</td></tr>';
    return;
  }
  const first3TripsByItinId = {};
  let processed = 0;
  trips.forEach((tripJkey) => {
    loadJsonFileAsObj(`./.visualizefiles/trips/${tripJkey}.json`, (trip) => {
      const itineraryId = trip['itinerary_id'];
      
      if (!first3TripsByItinId[itineraryId]) {
        first3TripsByItinId[itineraryId] = [];
      }
      if (first3TripsByItinId[itineraryId].length < 3) {
        first3TripsByItinId[itineraryId].push(trip);
      }

      processed += 1;
      if (processed === trips.length) {
        displayItineraries(first3TripsByItinId, routeJkey);
      }
    }, () => {
      console.log(`Could not find trip file for tripJkey ${tripJkey}`);

      processed += 1;
      if (processed === trips.length) {
        displayItineraries(first3TripsByItinId, routeJkey);
      }
    });
  });
}

// shows the itineraries and their (max 3) trips in the html, adding onclick events for each trip
function displayItineraries(first3TripsByItinId, routeJkey) {
  cachedTripInfo = {};
  Object.keys(first3TripsByItinId).forEach((itineraryId) => {
    const sorted3Trips = first3TripsByItinId[itineraryId].sort((a, b) => { return a['departure_time'].localeCompare(b['departure_time']); });
    let tableElement = '<tr><td class="itin_name">';
    
    const filePath = `./.visualizefiles/itineraries/${routeJkey}/itin_${itineraryId}.json`;
    loadJsonFileAsObj(filePath, (itin) => {
      tableElement += `${itin['itinerary_name']}:</td></tr><tr><td class="departure_times">`;
      
      sorted3Trips.forEach((trip) => {
        cachedTripInfo[trip['trip_jkey']] = trip;
        tableElement += `<span id="${trip['trip_jkey']}" class="departure_time" onclick="tripClicked(`;
        tableElement += `\'${itineraryId}\', \'${routeJkey}\', \'${trip['trip_jkey']}\')">`;
        tableElement += `${trip['departure_time']}</span>&nbsp;&nbsp;&nbsp;`;
      });

      tableElement += '</td></tr>';
      document.getElementById('itins_table').innerHTML += tableElement;
    }, () => {
      alert('Could not load itinerary file.');
    });
  });
}

// when a trip in the itinerary list is clicked, show it on the map and add the trip info div
function tripClicked(itineraryId, routeJkey, tripJkey) {
  clearTripInfo();
  if (activeTrip) {
    document.getElementById(activeTrip).style.color = '#91a5b0';
  }
  activeTrip = tripJkey;
  document.getElementById(activeTrip).style.color = '#30b566';
  displayItineraryWithDepTime(itineraryId, routeJkey, tripJkey);

  showTripInfo(tripJkey);
}

// function to call displayTrip with the required parameters
function displayItineraryWithDepTime(itineraryId, routeJkey, tripJkey) {
  clearMap();
  const filePath = `./.visualizefiles/itineraries/${routeJkey}/itin_${itineraryId}.json`;
  loadJsonFileAsObj(filePath, (itin) => {
    displayTrip(itin, tripJkey);
  }, () => {
    alert('Could not load itinerary file.');
  });
}

function addShapeToMap(json) {
  map.addSource('shape', {
    type: 'geojson',
    data: json,
  });
  
  map.addLayer({
    'id': 'shape',
    'type': 'line',
    'source': 'shape',
    'layout': {
      'line-join': 'round',
      'line-cap': 'round'
    },
    'paint': {
      'line-color': '#30b566',
      'line-width': 5
    }
  });

  map.addLayer({
    'id': "shape-line",
    "type": "symbol",
    "source": "shape",
    "layout": {
      "symbol-placement": "line",
      'text-font': ['Arial Unicode MS Regular'],
      'symbol-spacing': 200,
      'text-keep-upright': false,
      "text-field": '→',
      "text-size": 50 
    },
    "paint": {
      'text-color': '#14446b'
    }
  });

  shapeShown = true;
}

// given the itinerary and trip, show the trip on the map
function displayTrip(itin, tripJkey) {
  const trip = cachedTripInfo[tripJkey];

  if (!trip) {
    alert('Error loading trip while displaying to map.');
    return;
  }

  const stopList = itin['stop_list'];
  const timingList = trip['timing_list'];
  const depTime = trip['departure_time'];
  if (itin['shape_jkey']) {
    const filePath = `./.visualizefiles/shapes/${itin['shape_jkey']}.json`;
    
    loadJsonFileAsObj(filePath, (shapeJson) => {
      addShapeToMap(shapeJson);
      displayStopsAndZoomTo(stopList, timingList, depTime, shapeJson);
    }, () => {
      const shapeJson = createShapeOfStops(stopList);
      addShapeToMap(shapeJson);
      displayStopsAndZoomTo(stopList, timingList, depTime, shapeJson);
    });
  } else {
    const shapeJson = createShapeOfStops(stopList);
    addShapeToMap(shapeJson);
    displayStopsAndZoomTo(stopList, timingList, depTime, shapeJson);
  }
}

// add the stops to the map and zoom to the extent of the trip
function displayStopsAndZoomTo(stopList, timingList, depTime, shapeJson) {
  if (!stopList.length === timingList.length) {
    alert('Stop list and list of stop times are different lengths. Error in processed data.');
    return;
  }

  const stopJson = {'type': 'FeatureCollection', 'features': []};

  for (let i = 0; i < stopList.length; i += 1) {
    const stopInfo = stopList[i];
    const currentTime = getNextTime(depTime, timingList[i]);
    const stopFeature = {
      'type': 'Feature',
      'geometry': {
        'type': 'Point',
        'coordinates': [stopInfo[2], stopInfo[1]]
      },
      'properties': {
        'stop_id': stopInfo[0],
        'time': currentTime
      }
    };

    if (timingList[i] >= 0) {
      // Attach timepopup
      const timePopupOffsets = {
        'bottom': [0, -12.5],
      };
      const timePopup = new mapboxgl.Popup({ offset: timePopupOffsets, closeOnClick: false, closeButton: false })
        .setLngLat([stopInfo[2], stopInfo[1]])
        .setHTML(currentTime)
        .addTo(map);
  
      timePopups.push(timePopup);
    }
    stopJson['features'].push(stopFeature);
  }

  map.addSource('stops', {
    type: 'geojson',
    data: stopJson,
  });
  
  map.addLayer({
    'id': 'stops',
    'type': 'symbol',
    'source': 'stops',
    'layout': {
      'icon-image': 'custom-marker',
      'icon-size': .5,
    }
  });

  map.on('click', 'stops', function(e) {
    const coordinates = e.features[0].geometry.coordinates.slice();
    const stopId = e.features[0].properties.stop_id;
    const time = e.features[0].properties.time;

    createStopPopup(stopId, coordinates);
  });

  map.on('mouseenter', 'stops', function() {
    map.getCanvas().style.cursor = 'pointer';
  });
   
  map.on('mouseleave', 'stops', function() {
    map.getCanvas().style.cursor = '';
  });

  stopsShown = true;

  zoomToGeojson(shapeJson);
}

// when a stop is clicked, show relevant info from stops.txt
function createStopPopup(stopId, coordinates) {
  let content = '<div class="stop_popup_content">';

  // Attach timepopup
  const popupOffsets = {
    'bottom': [0, -7.5],
  };

  const pathToStopsFile = './.visualizefiles/stops/stops.json';
  loadJsonFileAsObj(pathToStopsFile, (stops) => {
    const stop = stops[stopId];

    if (!stop) {
      return content += '<span class="error">Could not get stop info.</span></div>';
    } else {
      content += `<span class="stop_name">${stop['stop_name']}</span> <span class="stop_id">(${stopId})</span><br>`;
      content += `${coordinates[0]},<br>${coordinates[1]}`;
      content += '</div>';
    }

    new mapboxgl.Popup({ offset: popupOffsets, closeButton: false })
      .setLngLat(coordinates)
      .setHTML(content)
      .addTo(map);
  }, () => {
    content += '<span class="error">Could not get stop info.</span></div>';

    new mapboxgl.Popup({ offset: popupOffsets, closeButton: false })
      .setLngLat(coordinates)
      .setHTML(content)
      .addTo(map);
  });
}
