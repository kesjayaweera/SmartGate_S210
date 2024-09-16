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

    var buttonopen = "<button class='control' id='open'>Open</button>";

    var buttonclose = "<button class='control' id='close'>Close</button>";

    vidwrapper.append(
        "<div id='cylebuttons'><div id='prevcontainer' class='buttoncontainer'>" + buttonprevious + "</div><div id='nextcontainer' class='buttoncontainer'>" + buttonnext + "</div></div>"
    );

    vidwrapper.append(
        "<div id='controlbuttons'><div id='opencontainer' class='buttoncontainer'>" + buttonopen + "</div><div id='closecontainer' class='buttoncontainer'>" + buttonclose + "</div></div>"
    );

    //Traverse through next camera stream
    $("#next").on("click", function () {
        counter = (counter + 1) % numberofcams;
        $("#footage").attr('src', "image" + camarr[counter] + ".jpg"); 
    });

    //Traverse through previous camera stream
    $("#previous").on("click", function () {
        counter = (counter - 1 + numberofcams) % numberofcams;
        $("#footage").attr('src', "image" + camarr[counter] + ".jpg"); 
    });

    //----- Send respective POST request to open or close door for manual intervention. -----
    //Example JSON format:
    // {"command" : "OPEN_DOOR"}
    // {"command" : "CLOSE_DOOR"}

    $("#open").on("click", function () {
        $.ajax({
            url: '/',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ command: "OPEN_DOOR" }),
            success: function(response) {
                console.log('[+] Open door command sent successfully');
            },
            error: function(xhr, status, error) {
                console.error('[-] Error sending open door command:', error);
            }
        });
    });

    $("#close").on("click", function () {
        $.ajax({
            url: '/',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ command: "CLOSE_DOOR" }),
            success: function(response) {
                console.log('[+] Close door command sent successfully');
            },
            error: function(xhr, status, error) {
                console.error('[-] Error sending close door command:', error);
            }
        });
    });

});
