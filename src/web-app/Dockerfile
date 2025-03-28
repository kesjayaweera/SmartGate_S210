# Use the official Alpine Linux Docker image
FROM alpine:latest

# Set the working directory
WORKDIR /SmartGate

# Enable the testing repository
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
# Enable the community repository
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories

# Install necessary packages
RUN apk update && \
    apk upgrade && \
    apk add bash git openssh sudo neofetch python3 postgresql uvicorn curl openrc fuse-overlayfs docker docker-cli-compose && \
    rm -rf /var/cache/apk/*  # Clean up cache

# Install necessary python packages
RUN apk add py3-flask py3-authlib py3-requests py3-psycopg py3-dotenv py3-fastapi 

# Allow root to use sudo without password
RUN echo "root ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/root

# Expose both Flask (5000) & PostgreSQL (5432)
EXPOSE 5000 5432

# Configure OpenRC and start Docker service
RUN openrc boot && \
    rc-update add docker default && \
    service docker start

# Start the Docker daemon
CMD ["sh", "-c", "dockerd --host=fd:// & sleep 3 && exec /bin/sh"]
