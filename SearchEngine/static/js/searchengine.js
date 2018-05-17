function openNav() {
    document.getElementById("mySidenav").style.width = "70%";
    // document.getElementById("flipkart-navbar").style.width = "50%";
    document.body.style.backgroundColor = "rgba(0,0,0,0.4)";
}

function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
    document.body.style.backgroundColor = "rgba(0,0,0,0)";
}
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}


function search_result() {
    $("body").css("cursor", "progress");
	ms = document.getElementById('pre-selected-options');
    var options = $('#pre-selected-options option:selected');
    var selected = {};
    for(var i=0;i<options.length;i++){
            selected[options[i].text] = options[i].value;
        }
    var search_query = document.getElementById('id_word').value;
    var exact_only = $('#someSwitchOptionInfo').prop('checked');
    var search_query = search_query.replace(/\s/g, '_');
    var csrftoken = getCookie('csrftoken');
    $.ajax({
        dataType: "json",
        url : "search_result/" + search_query, // the endpoint
        type : "POST", // http method
        data : { 'keyword' : search_query,
                 'exact_only': exact_only,
                 'selected': JSON.stringify(selected),
                 'csrfmiddlewaretoken': csrftoken }, // data sent with the post request

        // handle a successful response
        success : function(response) {
            document.open();
            document.write(response.html);
            document.close();
        },

        // handle a non-successful response
        error : function(xhr, errmsg, err) { 
            console.log(xhr.status + ": " + xhr.responseText);
    }
});
    $.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});
};