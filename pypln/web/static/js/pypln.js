function getURLParams() {
    var querystring = window.location.search.split('?')[1];
    var params = {}
    if (querystring != undefined){
        $(querystring.split('&')).each(function(idx, el){
            var key_value = el.split('=');
            var value = key_value[0];
            if (key_value[1] != undefined) {
                var key = key_value[1];
            } else {
                var key = true;
            }
            params[value] = key;
        })
    }
    return params;
}

$(document).ready(function() {
    $('#per-page').change(function(ev){
        window.location = "?per_page=" + ev.target.value;
    });
    $('.sort').click(function(ev) {
        var params = getURLParams();
        var element = ev.target;
        params['sort_by'] = element.getAttribute('key');
        if (element.classList.contains('sort_asc')) {
            params['sort_by'] = params.sort_by + "_desc";
        }
        // If you change the sort param, you probably want to be on the
        // first page.
        delete params.page;
        window.location = "?" + $.param(params);
    });
});
