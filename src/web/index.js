// JavaScript source code
$(document).ready(function () {

    var body = $("#body");

    var statswindow = $("#statswindow");

    var video = $("#video");

    var vidwrapper = $("#vidwrapper");

    var camarr = [1, 2, 3, 4];

    var counter = 0;

    var numberofcams = camarr.length;

    var buttonnext = "<button class='cycle' id='next'>Next &raquo;</button>";

    var buttonprevious = "<button class='cycle' id='previous'>&laquo; Previous</button>";

    vidwrapper.append(
        "<div id='buttons'><div id='prevcontainer' class='buttoncontainer'>" + buttonprevious + "</div><div id='nextcontainer' class='buttoncontainer'>" + buttonnext + "</div></div>"
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
