# Use the official Arch Linux Docker image
FROM archlinux:latest

# Set the working directory
WORKDIR /web-app

# Update the system
RUN pacman -Syy --noconfirm && \
    pacman -Syu --noconfirm && \
    pacman -Scc --noconfirm  # Clean up cache

# Keep the container running
CMD ["/bin/bash"]

