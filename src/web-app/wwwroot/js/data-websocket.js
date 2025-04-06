const socket = new WebSocket('ws://' + window.location.host + '/ws/user-overview');

socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    const userTable = document.getElementById('userTable').getElementsByTagName('tbody')[0];
    
    // Loop through the user data and update the table
    data.forEach(user => {
        const rowId = 'user-' + user.username;
        let row = document.getElementById(rowId);

        if (!row) {
            // If the row does not exist, create it
            row = userTable.insertRow();
            row.id = rowId;

            const cellUsername = row.insertCell(0);
            const cellRole = row.insertCell(1);

            cellUsername.innerText = user.username;
            cellRole.innerText = user.role_name;
        } else {
            // If the row exists, update the role or any other data if necessary
            row.cells[1].innerText = user.role_name;
        }
    });
};

socket.onopen = function () {
    console.log('WebSocket connection opened');
};

socket.onclose = function () {
    console.log('WebSocket connection closed');
};

socket.onerror = function (error) {
    console.log('WebSocket error: ' + error);
};
