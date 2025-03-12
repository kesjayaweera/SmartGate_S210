fetch("http://127.0.0.1:5000/test")
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error("SmartGate Backend Error: ", error))
