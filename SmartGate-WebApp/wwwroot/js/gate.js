document.addEventListener('DOMContentLoaded', () => {
    // Add emergency stop button to the page
    addEmergencyStopButton();
    
    // Select all camera feed elements
    const cameraFeeds = document.querySelectorAll('.camera-feed');

    cameraFeeds.forEach(feed => {
        const openBtn = feed.querySelector('.btn.open');
        const closeBtn = feed.querySelector('.btn.close');
        const statusText = feed.querySelector('.status');
        const gateText = feed.querySelector('.feed-info span').textContent;
        // Extract the gate number (only the number part) from the text
        const gateNo = gateText.match(/\d+/)[0];  // This extracts just the number (e.g., '1')
        // Extract just the status (Closed or Open) from the text content of the status element
        const currentStatus = statusText.textContent.split(':')[1]?.trim(); // This will extract 'Closed' or 'Open'
        
        // Add operation status indicator
        addOperationStatusIndicator(feed, gateNo);

        // Function to push gate data to the DB
        const pushGateDataToDb = async (gateNo, gateStatus) => {
            try {
                const response = await fetch('/add_gate_data', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        gate_no: gateNo,
                        gate_status: gateStatus,
                    }),
                });
                const data = await response.json();
                console.log('Gate data pushed:', data.message);
            } catch (error) {
                console.error('Error pushing gate data to DB:', error);
            }
        };
        
        pushGateDataToDb(gateNo, currentStatus)  

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
            
            const gateNo = feed.getAttribute('data-gate-no');

            // function to update gate status 
            // Chatgpt enter here:      
            const notifyBackendGateUpdate = async (gateNo, status) => {
                try {
                    const res = await fetch('/update_gate_data', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            gate_no: gateNo,
                            new_status: status,
                        }),
                    });
                    const data = await res.json();
                    console.log('Backend confirmed:', data.message);
                } catch (error) {
                    console.error('Backend update failed:', error);
                }
            };
            notifyBackendGateUpdate(gateNo, status.charAt(0).toUpperCase() + status.slice(1));
        };
        
        // Event listener for the OPEN button
        openBtn.addEventListener('click', () => {
            checkUserPermission('open_gate').then((allowed) => {
                if (allowed === null) {
                    alert("You need to log in to open the gate.");
                } else if (allowed) {
                    executeCommand('GATE_OPEN', gateNo);
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
                    executeCommand('GATE_CLOSE', gateNo);
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

// New command execution functions
async function executeCommand(commandType, gateNo) {
    try {
        const response = await fetch('/execute_command', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                command_type: commandType,
                gate_no: parseInt(gateNo),
                priority: 1
            })
        });

        const data = await response.json();
        if (response.ok) {
            console.log('Command submitted:', data.message);
            updateOperationStatus(gateNo, 'EXECUTING', commandType);
            
            // Monitor command status
            monitorCommandStatus(data.command_id, gateNo);
        } else {
            console.error('Command failed:', data.error);
            alert(`Command failed: ${data.error}`);
        }
    } catch (error) {
        console.error('Error executing command:', error);
        alert('Error executing command. Please try again.');
    }
}

async function monitorCommandStatus(commandId, gateNo) {
    const maxAttempts = 100; // Monitor for up to 10 seconds
    let attempts = 0;
    
    const checkStatus = async () => {
        try {
            const response = await fetch(`/command_status/${commandId}`);
            const data = await response.json();
            
            if (response.ok) {
                updateOperationStatus(gateNo, data.status, data.command_type);
                
                if (data.status === 'COMPLETED' || data.status === 'FAILED' || data.status === 'CANCELLED') {
                    // Command finished, stop monitoring
                    setTimeout(() => {
                        updateOperationStatus(gateNo, 'IDLE', null);
                    }, 2000);
                    return;
                }
            }
            
            attempts++;
            if (attempts < maxAttempts) {
                setTimeout(checkStatus, 100); // Check every 100ms
            }
        } catch (error) {
            console.error('Error monitoring command status:', error);
        }
    };
    
    checkStatus();
}

function updateOperationStatus(gateNo, status, commandType) {
    const statusIndicator = document.querySelector(`[data-gate-no="${gateNo}"] .operation-status`);
    if (statusIndicator) {
        statusIndicator.textContent = getStatusText(status, commandType);
        statusIndicator.className = `operation-status ${status.toLowerCase()}`;
    }
}

function getStatusText(status, commandType) {
    switch (status) {
        case 'EXECUTING':
            return commandType === 'GATE_OPEN' ? 'Opening...' : 
                   commandType === 'GATE_CLOSE' ? 'Closing...' : 'Processing...';
        case 'COMPLETED':
            return 'Completed';
        case 'FAILED':
            return 'Failed';
        case 'CANCELLED':
            return 'Cancelled';
        case 'IDLE':
        default:
            return 'Ready';
    }
}

function addOperationStatusIndicator(feed, gateNo) {
    const feedInfo = feed.querySelector('.feed-info');
    const statusIndicator = document.createElement('div');
    statusIndicator.className = 'operation-status idle';
    statusIndicator.textContent = 'Ready';
    statusIndicator.setAttribute('data-gate-no', gateNo);
    feedInfo.appendChild(statusIndicator);
}

function addEmergencyStopButton() {
    // Check if emergency stop button already exists
    if (document.getElementById('emergency-stop-btn')) {
        return;
    }
    
    const emergencyStopBtn = document.createElement('button');
    emergencyStopBtn.id = 'emergency-stop-btn';
    emergencyStopBtn.className = 'emergency-stop';
    emergencyStopBtn.textContent = 'EMERGENCY STOP';
    emergencyStopBtn.onclick = activateEmergencyStop;
    
    // Add to the top of the camera feeds section
    const cameraFeeds = document.querySelector('.camera-feeds');
    if (cameraFeeds) {
        cameraFeeds.parentNode.insertBefore(emergencyStopBtn, cameraFeeds);
    }
}

async function activateEmergencyStop() {
    if (!confirm('Are you sure you want to activate emergency stop? This will halt all gate operations immediately.')) {
        return;
    }
    
    try {
        const response = await fetch('/emergency_stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();
        if (response.ok) {
            alert('Emergency stop activated! All operations have been halted.');
            
            // Update all gate status indicators
            document.querySelectorAll('.operation-status').forEach(indicator => {
                indicator.textContent = 'Emergency Stop';
                indicator.className = 'operation-status emergency';
            });
        } else {
            alert(`Emergency stop failed: ${data.error}`);
        }
    } catch (error) {
        console.error('Error activating emergency stop:', error);
        alert('Error activating emergency stop. Please try again.');
    }
}
