const socket = window.socket;

socket.onopen = function () {
    console.log('WebSocket connection opened');

    // Send an event to request "user_overview" data
    socket.send(JSON.stringify({ event: "user_overview" }));
};

// Listen for incoming messages from the WebSocket
socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    
    // If the event is user_overview, handle the data
    if (data.event === "user_overview") {
        updateUserOverviewTable(data.data);
    }
};

function updateUserOverviewTable(data) {
    const userTable = document.getElementById('userTable').getElementsByTagName('tbody')[0];
    
    // Loop through the user data and update the table
    data.forEach(user => {
        const rowId = 'user-' + user.username;
        let row = document.getElementById(rowId);

        if (!row) {
            row = userTable.insertRow();
            row.id = rowId;

            // Set a data-username attribute for each row
            row.setAttribute('data-username', user.username);

            const cellUsername = row.insertCell(0);
            const cellRole = row.insertCell(1);
            const cellStatus = row.insertCell(2);
            const cellAction = row.insertCell(3);

            cellUsername.innerText = user.username;
            cellRole.innerText = user.role_name;
            cellStatus.className = 'status';
            cellStatus.innerText = user.status;
            cellAction.innerHTML = `<button onclick="removeUser('${user.username}')">Remove</button>`;
        } else {
            row.cells[1].innerText = user.role_name;
            row.cells[2].innerText = user.status;
        }
    });
}

// Open role modal on row click
document.getElementById("userTable").addEventListener("click", function (e) {
    const row = e.target.closest("tr");
    if (!row || e.target.tagName === "BUTTON") return;

    const selectedUsername = row.getAttribute('data-username'); // Retrieve username from data-attribute
    document.getElementById("modalUsername").innerText = `Username: ${selectedUsername}`;
    document.getElementById("roleModal").style.display = "block";
});

// Close modal
document.getElementById("closeModal").onclick = function () {
    document.getElementById("roleModal").style.display = "none";
};

// Close modal if clicking outside the modal
window.onclick = function (event) {
    if (event.target === document.getElementById("roleModal")) {
        document.getElementById("roleModal").style.display = "none";
    }
};

document.getElementById("saveRole").addEventListener("click", function () {
    // Example of handling saving the role (e.g., after editing)
    let something = undefined; // or let something = null;
    // You can call an API or WebSocket to save the role changes here
});

socket.onclose = function () {
    console.log('WebSocket connection closed');
};

socket.onerror = function (error) {
    console.log('WebSocket error: ' + error);
};
