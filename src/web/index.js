// JavaScript source code
$(document).ready(function () {

    var body = $("#body");

    var statswindow = $("#statswindow");

    var video = $("#video");

    var camarr = [1, 2, 3, 4];

    var counter = 0;

    var numberofcams = camarr.length;

    var buttonnext = "<button id='next'>Next &raquo;</button>";

    var buttonprevious = "<button id='previous'>&laquo; Previous</button>";

    body.append(
        buttonprevious + buttonnext
    );
    $("#next").on("click", function () {
        if (counter + 1 >= numberofcams) {
            counter = 0;
        $("#footage").attr("src", "image1.jpg");
        } else {
            counter++;
            var nextcam = counter + 1;
            $("#footage").attr('src', ("image" + nextcam + ".jpg"))
        }     
    });

    $("#previous").on("click", function () {
        if (counter - 1 < 0) {
            counter = 3;
            $("#footage").attr("src", "image4.jpg");
        } else {
            counter--;
            var nextcam = counter + 1;
            $("#footage").attr('src', ("image" + nextcam + ".jpg"))
        }
    });

    

});