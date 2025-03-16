# Use the official Arch Linux Docker image
FROM archlinux:latest

# Set the working directory
WORKDIR /web-app

# Update the system to stay in sync with the latest Arch Linux packages
RUN pacman -Syu --noconfirm && \
    pacman -Scc --noconfirm  # Clean up cache

# Keep the container running
CMD ["/bin/bash"]

