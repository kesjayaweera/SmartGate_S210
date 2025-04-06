const socket = new WebSocket('ws://' + window.location.host + '/ws/user-overview');
let selectedUsername = '';

socket.onmessage = function (event) {
    const data = JSON.parse(event.data);
    const userTable = document.getElementById('userTable').getElementsByTagName('tbody')[0];
    
    // Loop through the user data and update the table
    data.forEach(user => {
        const rowId = 'user-' + user.username;
        let row = document.getElementById(rowId);

        if (!row) {
            row = userTable.insertRow();
            row.id = rowId;

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

        // Update Status Later
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

// Open role modal on row click
document.getElementById("userTable").addEventListener("click", function (e) {
    const row = e.target.closest("tr");
    if (!row || e.target.tagName === "BUTTON") return;

    selectedUsername = row.cells[0].innerText;
    document.getElementById("modalUsername").innerText = `Username: ${selectedUsername}`;
    document.getElementById("roleModal").style.display = "block";
});

// Close modal
document.getElementById("closeModal").onclick = function () {
    document.getElementById("roleModal").style.display = "none";
};

window.onclick = function (event) {
    if (event.target === document.getElementById("roleModal")) {
        document.getElementById("roleModal").style.display = "none";
    }
};

document.getElementById("saveRole").addEventListener("click", function () {
    let something = undefined; // or let something = null;
});
