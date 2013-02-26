$(document).ready(function() {
    $('#per-page').change(function(ev){
        window.location = "?per_page=" + ev.target.value;
    });
});
