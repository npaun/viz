// file with all of the event listeners for the inputs in the top left

function addInputEventListeners() {
  document.getElementById('date_search').addEventListener('keyup', onDateKeyup, false);
  document.getElementById('time_search').addEventListener('keyup', onTimeKeyup, false);
  document.getElementById('trip_search').addEventListener('keyup', onTripKeyup, false);
}

function onDateKeyup(e) {
  // 13 is the enter key
  if (e.keyCode === 13) {
    e.preventDefault();
    document.getElementById('datebutton').click();
  }
}

function onTimeKeyup(e) {
  // 13 is the enter key
  if (e.keyCode === 13) {
    e.preventDefault();
    document.getElementById('timebutton').click();
  }
}

function onTripKeyup(e) {
  // 13 is the enter key
  if (e.keyCode === 13) {
    e.preventDefault();
    document.getElementById('tripbutton').click();
  }
}

// When a date is entered
function onEnterDate() {
  selectedDate = document.getElementById('date_search').value;
  if (selectedDate.length > 0) {
    addInputData('date_search', 'date_entered', 'datebutton', selectedDate);
  }
  if (activeRouteInfo) {
    const { routeJkey, routeShortName } = activeRouteInfo;
    clearRoute();
    routeClicked(routeJkey, routeShortName);
  }
}

// When a time is entered
function onEnterTime() {
  selectedTime = document.getElementById('time_search').value;
  if (selectedTime.length > 0) {
    addInputData('time_search', 'time_entered', 'timebutton', selectedTime);
  }
  if (activeRouteInfo) {
    const { routeJkey, routeShortName } = activeRouteInfo;
    clearRoute();
    routeClicked(routeJkey, routeShortName);
  }
}

// When a trip id is entered
function onEnterTripId() {
  const tripId = document.getElementById('trip_search').value;
  if (tripId.length > 0) {
    loadJsonFileAsObj(`/.visualizefiles/trip_index/${tripId}.json`,
        (tripJkey) => {
    addInputData('trip_search', 'trip_entered', 'tripbutton', tripId);
    showTrip(tripJkey);
        },
        () => { alert('Cannot load trip ID mappings'); }
    );
  }
}

// Generic function to show what was entered in the date, time, or trip id inputs
function addInputData(inputDiv, textDiv, button, text) {
  document.getElementById(inputDiv).style.display = 'none';
  document.getElementById(button).style.display = 'none';
  document.getElementById(textDiv).innerHTML = text;
  document.getElementById(textDiv).style.display = 'inline-block';
}

// Shows the input element when the user wants to change the date, time, or trip id
function inputClicked(inputDiv, textDiv, button) {
  document.getElementById(textDiv).style.display = 'none';
  document.getElementById(inputDiv).style.display = 'inline';
  addInputEventListeners();
  document.getElementById(button).style.display = 'inline';
  document.getElementById(inputDiv).focus();
}

