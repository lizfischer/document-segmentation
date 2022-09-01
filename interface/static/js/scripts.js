$(document).ready( function() {

    // Modal Closing Buttons
    $('.modal-close').click(function (){
        $(this).closest('.modal').removeClass("active");
    });

    /* FLASH */
    $('.toast').delay(5000).fadeOut(); // Stay for 5 seconds, then fade
    $(".toast .btn-clear").click(function (){ // Allow manual close
        $(this).parent().hide();
    });

});