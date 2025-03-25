# Use the official Arch Linux Docker image
FROM archlinux:latest

# Set the working directory
WORKDIR /SmartGate

# Update the system
RUN pacman -Syy --noconfirm && \
    pacman -Syu --noconfirm && \
    pacman -Scc --noconfirm  # Clean up cache

# Expose both Flask (5000) & PostgreSQL (5432)
EXPOSE 5000 5432

# Keep the container running
CMD ["/bin/bash"]

