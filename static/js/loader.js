window.onunload = function(){};

window.onload = function() {
    document.body.style.cursor='auto';
    document.getElementById('content').style.pointerEvents = 'auto';
}


function setLoading() {
    document.body.style.cursor = 'wait';
    document.getElementById('content').style.pointerEvents = 'none';
}
