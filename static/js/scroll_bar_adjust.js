function viewportToPixels(value) {
    var parts = value.match(/([0-9\.]+)(vh|vw)/)
    var q = Number(parts[1])
    var side = window[['innerHeight', 'innerWidth'][['vh', 'vw'].indexOf(parts[2])]]
    return side * (q/100)
}


window.setInterval(function adjustScrollBar() {
    var scroll_bar_height = (window.innerHeight-$(window).height());
    var html_body = document.getElementsByTagName('body')[0];
    var new_height = viewportToPixels('100vh') - scroll_bar_height;
    html_body.style.height = new_height + 'px';
}, 1);
