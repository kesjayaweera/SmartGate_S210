document.addEventListener('DOMContentLoaded', () => {
  // Select all camera feed elements
  const cameraFeeds = document.querySelectorAll('.camera-feed');

  cameraFeeds.forEach(feed => {
    const openBtn = feed.querySelector('.btn.open');
    const closeBtn = feed.querySelector('.btn.close');
    const statusText = feed.querySelector('.status');
    const gateImage = feed.querySelector('.gate-image');

    // Function to update the gate status
    const updateGateStatus = (status) => {
      feed.setAttribute('data-status', status);
      statusText.textContent = `Status: ${status.charAt(0).toUpperCase() + status.slice(1)}`;
      statusText.className = `status ${status}`;

      // Update button active states
      if (status === 'open') {
        openBtn.classList.add('active');
        closeBtn.classList.remove('active');
        // Update image background color to green
        gateImage.src = gateImage.src.replace(/F44336|4CAF50/, '4CAF50');
      } else {
        closeBtn.classList.add('active');
        openBtn.classList.remove('active');
        // Update image background color to red
        gateImage.src = gateImage.src.replace(/F44336|4CAF50/, 'F44336');
      }
    };

    // Event listener for the OPEN button
    openBtn.addEventListener('click', () => {
      updateGateStatus('open');
    });

    // Event listener for the CLOSE button
    closeBtn.addEventListener('click', () => {
      updateGateStatus('closed');
    });
  });
});
