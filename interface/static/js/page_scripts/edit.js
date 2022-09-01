$(document).ready(function (){
    /** Update Steps **/
    $(".step-item").removeClass("active");
    $("#edit").addClass("active");



    $('#doc-id').focus();
    // Trigger "next" on enter in id field
    $('#doc-id').keypress(function (e) {
     var key = e.which;
     if(key == 13)  // the enter key code
      {
        $('#next-btn').click();
        return false;
      }
    });
    // Copy ID from body on alt-I
    $('#document-text').keydown(function (e) {
        if (e.keyCode == 73 && e.altKey) // alt-i
        {
            e.preventDefault();
            let start = $('#document-text').prop("selectionStart");
            let finish = $('#document-text').prop("selectionEnd");
            let sel = $('#document-text').val().substring(start, finish);
            $("#doc-id").val(sel.trim().replace(/ +/gm," "));
            $('#doc-id').focus();
            return false;
        }
    });
    /* next */
    $("#next-btn").click(function (){
        d = {
            action: "save",
            save: $("#document-text").val(),
            entry: entry_id, // assigned in edit.html via jinja template
            name: $("#doc-id").val()
        }

        post_edits(d, function (){
            window.location.href = next_url;
        });
    });
    /* previous */
    $("#prev-btn ").click(function (){
        d = {
            action: "save",
            save: $("#document-text").val(),
            entry: entry_id,
            name: $("#doc-id").val()
        }

        post_edits(d, function (){
            window.location.href = prev_url;
        });
    });

    /* Find and replace */
    $("#find-replace").click(function (){
       $("#find-replace-wrapper").toggle();
    });

    $("#do-replace").click(function (){
        const allowed_special_characters = ["\n", "\t"]
        let find = RegExp($("#find-regex").val(), 'gm');
        let rep = $("#replace-regex").val().replace("\\n", "\n").replace("\\t", "\t");

        $("#document-text").val(
            $("#document-text").val().replace(find, rep)
        )
    });
    $('#replace-regex').keypress(function (e) {
     var key = e.which;
     if(key == 13)  // the enter key code
      {
        $('#do-replace').click();
        return false;
      }
    });

    /* "Undo" */
    $("#undo").click(function (){
       window.location.reload(true);
    });

    /* Trigger split */
    $("#split-at").click(function (){
        var split_at = $("#document-text").prop("selectionStart");
        new_start_page = window.prompt("New entry starts on page:", "");

        if (!isNaN(new_start_page) && new_start_page){
            post_edits({
                action: "split",
                split_page: new_start_page,
                offset: split_at,
                text: $("#document-text").val(),
                entry: entry_id
            }, function (){
                window.location.href = entry_url;
            });
        }
    });

    /* Trigger join */
    $("#join").click(function (){
        post_edits({
            action: "join",
            text: $("#document-text").val(),
            entry: entry_id
        }, function (){
            window.location.href = prev_url;
        });
    });


    /* Save text */
    $("#save").click(function (){
        d = {
            action: "save",
            save: $("#document-text").val(),
            entry: entry_id,
            name: $("#doc-id").val()
        }

        post_edits(d, function (){
            window.location.href = entry_url;
        });
    });

    /* Delete text */
    $("#delete-entry").click(function (){
        if (confirm("Are you sure you want to delete this entry?")) {
            d = {
                action: "delete",
                entry: entry_id
            }

            post_edits(d, function () {
                window.location.href = next_url;
            });
        }
    });

    function post_edits(data, callback=null){
        var xhr = new XMLHttpRequest();
        xhr.open("POST", post_url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.onreadystatechange = function () {
          if (xhr.readyState === XMLHttpRequest.DONE) {
              if (callback) {
                  callback();
              }
          }};

        xhr.send(JSON.stringify(data));
    }

});