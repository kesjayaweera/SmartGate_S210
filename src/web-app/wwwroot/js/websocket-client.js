// Create a WebSocket connection to the server's live-data route
const socket = new WebSocket('ws://' + window.location.host + '/ws/live-data');

// Event handler for when the WebSocket connection is opened
socket.onopen = function () {
    console.log('WebSocket connection opened');

    // Send the 'user_overview' event after the connection is established
    const message = {
        event: 'user_overview'
    };
    socket.send(JSON.stringify(message));
};

// Event handler for when the WebSocket receives a message
socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    console.log('Received data:', data);
};

// Event handler for when the WebSocket connection is closed
socket.onclose = function () {
    console.log('WebSocket connection closed');
};

// Event handler for when an error occurs with the WebSocket connection
socket.onerror = function (error) {
    console.error('WebSocket error:', error);
};
