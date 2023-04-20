$(document).ready( function() {

    // Rename Modal
    $('#rename-btn').click(function () {
        $("#rename-modal").addClass("active");
    });

    // Rename submit
    $("#submit-rename").click(submit_rename);
    $("#new_name").on("keydown", function (e) {
        if (e.which == 13) {
            submit_rename();
        }
    });

    function submit_rename() {
        const new_name = $("#new_name").val();
        if (!new_name) {
            document.getElementById("rename_form").classList.add("has-error");
        } else {
            document.getElementById("rename_form").classList.remove("has-error");
            const form = $("#rename_form").submit();
        }
    }


    // Delete Modal
    $('#delete').click(function () {
        $("#delete-prompt").addClass("active");
    });


    // Processing functions
    function finished_binarize(data) {
        console.log("Binarize: " + data["status"]);
    }

    function finished_margins(data) {
        console.log("Finished preparing margins");
        const start = data["preview"]["start"];
        const end = data["preview"]["end"];
        const url = `/{{project.id}}/threshold-preview?t=${data["thresh_id"]}&start=${start}&end=${end}`;
        window.location.href = url;
    }
});