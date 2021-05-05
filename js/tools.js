// random tools needed

// load json file and parse as object, call onSuccess with json object if success
function loadJsonFileAsObj(path, onSuccess, onFail) {
  var xhr = new XMLHttpRequest();
  xhr.onreadystatechange = () => {
    if (xhr.readyState === XMLHttpRequest.DONE) {
      if (xhr.status === 200) {
        onSuccess(JSON.parse(xhr.responseText));
      } else {
        onFail();
      }
    }
  };
  xhr.open("GET", path + '?cache=' + cacheId, true);
  xhr.send();
  addInputEventListeners(); 
}

// calculate the time after a HH:MM:SS given a number of seconds after it
function getNextTime(prevTime, secOffset) {
  timeSplit = prevTime.split(':');
  const hh = parseInt(timeSplit[0]);
  const mm = parseInt(timeSplit[1]);
  const ss = parseInt(timeSplit[2]);
  const originalTimeSeconds = ss + mm * 60 + hh * 60 * 60;
  const nextTime = originalTimeSeconds + secOffset;
  let finalSeconds = nextTime % 60;
  let finalMinutes = Math.floor(nextTime / 60);
  const finalHours = Math.floor(finalMinutes / 60);
  finalMinutes = finalMinutes % 60;

  if (finalSeconds < 10) {
    finalSeconds = '0' + finalSeconds.toString();
  }
  if (finalMinutes < 10) {
    finalMinutes = '0' + finalMinutes.toString();
  }

  return `${finalHours}:${finalMinutes}:${finalSeconds}`;
}

// map manipulation tools
function zoomToGeojson(geojson) {
  const coordinates = geojson['geometry']['coordinates'];
  const bounds = coordinates.reduce(function(bounds, coord) {
    return bounds.extend(coord);
  }, new mapboxgl.LngLatBounds(coordinates[0], coordinates[0]));
  map.fitBounds(bounds, {
    padding: {top: 25, bottom: 25, left: 300, right: 25},
    linear: true,
  });
}

function removeShape() {
  map.removeLayer('shape');
  map.removeLayer('shape-line');
  map.removeSource('shape');

  shapeShown = false;
}

function removeStops() {
  map.removeLayer('stops');
  map.removeSource('stops');

  timePopups.forEach((popup) => {
    popup.remove();
  });

  timePopups = [];
  stopsShown = false;
}

function clearMap() {
  if (shapeShown) removeShape();
  if (stopsShown) removeStops();
}

// geographic tools

// given a stop list, create a geojson of lines between the stops
function createShapeOfStops(stopList) {
  const shapeJson = {
    'type': 'Feature',
    'geometry': {
      'type': 'LineString',
      'properties': {},
      'coordinates': [],
    },
  };

  stopList.forEach((stopInfo) => {
    shapeJson['geometry']['coordinates'].push([stopInfo[2], stopInfo[1]]);
  });

  return shapeJson;
}

