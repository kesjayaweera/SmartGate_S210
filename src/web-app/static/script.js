// Fetch the JSON data from /test
fetch("/test")
    .then(response => response.json())  // Convert response to JSON
    .then(data => {
        // Update the page with the JSON data
        document.getElementById("message").innerText = data.message;
        document.getElementById("status").innerText = data.status;
    })
    .catch(error => console.error("Error fetching status:", error));
