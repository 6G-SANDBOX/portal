$(document).ready(
    function () {
        if(window.location.href.indexOf("reload") > -1) {
            $( ".opaque" ).show();
            $( ".loader" ).show();
            setTimeout(function(){location.replace(window.location.href.replace("/reload",""));},4000);
        }
    }
);
$(document).ready(
    function () {
        if(window.location.href.indexOf("reloadLog") > -1) {
            $( ".opaque" ).show();
            $( ".loader" ).show();
            setTimeout(function(){location.replace(window.location.href.replace("/reloadLog",""));},2000);
        }
    }
);

function updateOne(element, newValue){
    if (element.text() !== newValue){
        element.text(newValue);
        element.addClass('highlight');
        setTimeout(function(){element.removeClass('highlight');},3000);
    }
}

function updatePerCent(nanobar, percent, hidden){
    if (percent.toString() !== hidden.text()){
        nanobar.go(percent);
        hidden.text(percent);
    }
}

function updateMessage(element, msg){
    let message = '...';
    if (msg.length !== 0){ message = msg; }
    if (element.text() !== message){ element.text(message); }
}