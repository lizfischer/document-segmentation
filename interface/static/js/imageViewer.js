function initViewer(images, start_adjustment=0,url_for=true, start_pg=0){

    var currentImg = 0;
    var img = new Image();
    img.id = 'activeImage';
    img.src = images[currentImg];
    goTo(currentImg);


    var nextButton = $('<i></i>', {
        class: 'btn fa-solid fa-angle-right',
        id: 'nextBtn',
        on: {
            click: nextImage
        }
    });
    var prevButton = $('<i></i>', {
        class: 'btn fa-solid fa-angle-left',
        id: 'prevBtn',
        on: {
            click: previousImage
        }
    });
    var firstButton = $('<i></i>', {
        class: 'btn fa-solid fa-angles-left',
        id: 'nextBtn',
        on: {
            click: firstImage
        }
    })
    var lastButton = $('<i></i>', {
        class: 'btn fa-solid fa-angles-right',
        id: 'nextBtn',
        on: {
            click: lastImage
        }
    })
    var pgNum = $('<input />', {
        type: 'text',
        value: currentImg + 1 + start_adjustment,
        id: 'currentPg',
        size: 2
    });
    pgNum.change(function (){
        goTo($(this).val()-1)
    })

    function goTo(n) {
        if (0 <= n && n <= images.length){
            currentImg = n;
            $('#currentPg').val(currentImg+1+start_adjustment);
            $('#activeImage').attr("src", images[currentImg]);
        } else {
            console.log("out of bounds!");
            $('#currentPg').val(currentImg+1);
        }
    }
    function nextImage() {
        if (currentImg < images.length-1) {
            goTo(currentImg+1);
        }
        console.log(currentImg)
    }
    function previousImage() {
        if (currentImg > 0) {
            goTo(currentImg-1);
        }
        console.log(currentImg)
    }
    function firstImage() {
        goTo(0)
    }
    function lastImage() {
        goTo(images.length-1);
    }

    var topBar = $('<div />', {
        id: 'viewer-controls'
    }).appendTo("#imgviewer");

    $("#viewer-controls").append(firstButton);
    $("#viewer-controls").append(prevButton);
    $("#viewer-controls").append(pgNum);
    $("#viewer-controls").append(nextButton);
    $("#viewer-controls").append(lastButton);
    $("#imgviewer").append(img);
    console.log("Done!")
    goTo(start_pg);
}


function waitForElm(selector) {
    return new Promise(resolve => {
        if (document.querySelector(selector)) {
            return resolve(document.querySelector(selector));
        }

        const observer = new MutationObserver(mutations => {
            if (document.querySelector(selector)) {
                resolve(document.querySelector(selector));
                observer.disconnect();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
}