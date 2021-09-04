window.onload = updateNavigationWidth;


/**
 * Bodging to fixup the navigation bar width
 */
function updateNavigationWidth() {
    var navigation_bar = document.getElementById('navigation');
    var elements = document.getElementsByClassName("navigation_element");
    var total_elements_width = 0
    for (var i = 0; i < elements.length; i++) {
        total_elements_width += elements[i].offsetWidth;
    }
    navigation_bar.style.width = total_elements_width.toString(10)+"px";
}
