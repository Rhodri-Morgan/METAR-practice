const value = JSON.parse(document.getElementById('airport_location').textContent);

window.onload = map_initialize;

// Google function for adding map
function map_initialize() {
  var airport = { lat: value['latitude'], lng: value['longitude'] };

  var map_config = {
      zoom : 12,
      center : airport,
      mapTypeId : 'hybrid',
      fullscreenControl: false,
      streetViewControl: false,
      zoomControl: false,
      mapTypeControl: false
  }

  var map = new google.maps.Map(document.getElementById('map'), map_config);

  var marker = new google.maps.Marker({
    position: airport,
    map: map,
  });
}


function reveal_answer() {
  document.getElementById('answer_revealer').style.display = 'none';
  document.getElementById('answer_container').style.display = 'block';
  document.getElementById('answer_container').classList.add('fade_in_effect');
}


function refresh_page() {
  var description_value = document.getElementById('description_text_area').value;
  if (description_value != "") {
    document.getElementById("submit_report_form").click();
  } else{
    window.location.reload(false);
  }
}
