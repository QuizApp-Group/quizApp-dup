function resource_error(element) {
    var fallback_url = element.dataset.fallback;
    console.log("Fallback: " + fallback_url);
    var is_js = fallback_url.substr(fallback_url.length - 3) == ".js";
    if(is_js) {
        var script = document.createElement('script');
        script.src = fallback_url;
        document.head.appendChild(script);
    } else {
        var link = document.createElement('link');
        link.href = fallback_url;
        link.rel = "stylesheet";
        document.head.appendChild(link);
    }
}

function check_js_error(condition, fallback) {
    if(!condition) {
        var script = document.createElement('script');
        script.src = fallback_url;
        document.head.appendChild(script);
    }
}
