const value = JSON.parse(document.getElementById('airport_location').textContent);

// Google function for adding map
function initMap() {
  var airport = { lat: value['latitude'], lng: value['longitude'] };

  var map_config = {
      zoom : 12,
      center : airport,
      mapTypeId : 'hybrid'
  }

  var map = new google.maps.Map(document.getElementById('map'), map_config);

  var marker = new google.maps.Marker({
    position: airport,
    map: map,
  });
}


function reveal_answer() {
  document.getElementById('answer_revealer').style.display = "none";
  document.getElementById('answer_container').style.display = "block";
  document.getElementById('answer_container').classList.add('fade_in_class')
}


function refresh_page(){
  window.location.reload();
}
