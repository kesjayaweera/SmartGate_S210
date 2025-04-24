document.addEventListener('DOMContentLoaded', () => {
    // Select all camera feed elements
    const cameraFeeds = document.querySelectorAll('.camera-feed');

    cameraFeeds.forEach(feed => {
        const openBtn = feed.querySelector('.btn.open');
        const closeBtn = feed.querySelector('.btn.close');
        const statusText = feed.querySelector('.status');

        // Function to update the gate status
        const updateGateStatus = (status) => {
            feed.setAttribute('data-status', status);
            statusText.textContent = `Status: ${status.charAt(0).toUpperCase() + status.slice(1)}`;
            statusText.className = `status ${status}`;

            // Update button active states
            if (status === 'open') {
                openBtn.classList.add('active');
                closeBtn.classList.remove('active');
            } else {
                closeBtn.classList.add('active');
                openBtn.classList.remove('active');
            }
        };
        
        // Event listener for the OPEN button
        openBtn.addEventListener('click', () => {
            checkUserPermission('open_gate').then((allowed) => {
                if (allowed === null) {
                    alert("You need to log in to open the gate.");
                } else if (allowed) {
                    updateGateStatus('open');
                } else {
                    alert("You don't have permission to open the gate.");
                }
            }).catch((error) => {
                console.error("Error checking permission:", error);
            });
        });

        // Event listener for the CLOSE button
        closeBtn.addEventListener('click', () => {
            checkUserPermission('close_gate').then((allowed) => {
                if (allowed === null) {
                    alert("You need to log in to close the gate.");
                } else if (allowed) {
                    updateGateStatus('closed');
                } else {
                    alert("You don't have permission to close the gate.");
                }
            }).catch((error) => {
                console.error("Error checking permission:", error);
            });
        });

    });
});

async function checkUserPermission(permission) {
    try {
        const userResponse = await fetch('/get-username');
        const userData = await userResponse.json();
        if (userData.error) {
            return null; // Not logged in
        }

        const username = userData.username;
        const permissionResponse = await fetch(`/check-permission?username=${username}&perm_name=${permission}`);
        const permissionData = await permissionResponse.json();

        return permissionData.allowed;
    } catch (error) {
        console.error("Error checking permission:", error);
        return false;
    }
}
