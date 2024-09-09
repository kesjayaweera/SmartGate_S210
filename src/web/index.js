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
        counter = (counter + 1) % numberofcams;
        $("#footage").attr('src', "image" + camarr[counter] + ".jpg"); 
    });

    $("#previous").on("click", function () {
        counter = (counter - 1 + numberofcams) % numberofcams;
        $("#footage").attr('src', "image" + camarr[counter] + ".jpg"); 
    });

});
