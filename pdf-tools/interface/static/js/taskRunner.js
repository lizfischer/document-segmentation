function start_long_task(task_type, project_id, data=null, callback=null) {
        // add task status elements
        div = $('<div class="progress"><div></div><div>0%</div><div>...</div><div>&nbsp;</div></div><hr>');
        $('#progress').append(div);

        // create a progress bar
        var nanobar = new Nanobar({
            bg: '#44f',
            target: div[0].childNodes[0]
        });

        // send ajax POST request to start background job
       $.ajax({
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({"type": task_type, "project_id": project_id, "data": data}),
            url: "/delegate",
            success: function(data, status, request) {
                update_progress(data['task_id'], nanobar, div[0], callback);
            },
            error: function() {
                alert('Unexpected error');
            }
        });
    }

function update_progress(task_id, nanobar, status_div, callback=null) {
    // send GET request to status URL
    $.getJSON(`/status/${task_id}`, function(data) {
        // update UI
        percent = parseInt(data['current'] * 100 / data['total']);
        nanobar.go(percent);
        $(status_div.childNodes[1]).text(percent + '%');
        $(status_div.childNodes[2]).text(data['status']);
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
                update_progress(task_id, nanobar, status_div, callback);
            }, 2000);
        }
    });
}