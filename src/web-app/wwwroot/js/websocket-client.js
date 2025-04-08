// Check if there's already an existing WebSocket connection
if (!window.socket) {
    // Create a WebSocket connection to the server's live-data route
    window.socket = new WebSocket('ws://' + window.location.host + '/ws/live-data');
    
    // Event handler for when the WebSocket connection is opened
    window.socket.onopen = function () {
        console.log('WebSocket connection opened');
    };

    // Event handler for when the WebSocket connection is closed
    window.socket.onclose = function () {
        console.log('WebSocket connection closed');
    };

    // Event handler for when an error occurs with the WebSocket connection
    window.socket.onerror = function (error) {
        console.error('WebSocket error:', error);
    };
} else {
    console.log("WebSocket connection already exists.");
}
