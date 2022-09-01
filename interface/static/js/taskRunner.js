function update_bar(pct, message=null){
    let bar = $("#progress .bar div[role='progressbar']")
    bar.width(pct+'%');
    bar.attr('aria-valuenow', pct);
    bar.text(pct+"%");
    if (message){
        $("#progress .bar-message").text(message);
    } else {
        $("#progress .bar-message").text("");
    }
}

function init_bar(){
    if (!$("#progress .bar").length){
        const bar = `<div class="bar">
                    <div class="bar-item" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0""></div>
                </div>
                <div class="bar-message"></div>`
        $("#progress").append(bar);
    }
    update_bar(0);
}

function start_long_task(task_type, project_id, data=null, callback=null) {

        /* create a progress bar */
        init_bar();
        /*var nanobar = new Nanobar({
            bg: '#44f',
            target: div[0].childNodes[0]
        });*/

        // send ajax POST request to start background job
       $.ajax({
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({"type": task_type, "project_id": project_id, "data": data}),
            url: "/delegate",
            success: function(data, status, request) {
                update_progress(data['task_id'], callback);
            },
            error: function() {
                alert('Unexpected error');
            }
        });
    }

function update_progress(task_id, callback=null) {
    // send GET request to status URL
    $.getJSON(`/status/${task_id}`, function(data) {
        // update UI
        percent = parseInt(data['current'] * 100 / data['total']);

       // nanobar.go(percent);

        update_bar(percent, data['status']);
        //$(status_div.childNodes[1]).text(percent + '%');
        //$(status_div.childNodes[2]).text(data['status']);

        if (data['state'] != 'PENDING' && data['state'] != 'PROGRESS') {
            if ('result' in data) {
                // print result
                console.log("result");
                if(callback){
                    callback(data["result"]);
                }

            }
            else {
                // something unexpected happened
                $(status_div.childNodes[3]).text(data['state']);
            }
        }
        else {
            // rerun in 2 seconds
            setTimeout(function() {
                update_progress(task_id, callback);
            }, 2000);
        }
    });
}