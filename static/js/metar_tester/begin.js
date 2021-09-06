const value = JSON.parse(document.getElementById('airport_location').textContent);

// Google function for adding map
function initMap() {
    var airport = { lat: value['latitude'], lng: value['longitude'] };

    var map_config = {
        zoom : 12,
        center : airport,
        mapTypeId : 'hybrid'
    }

    var map = new google.maps.Map(document.getElementById("map"), map_config);

    var marker = new google.maps.Marker({
      position: airport,
      map: map,
    });
  }
