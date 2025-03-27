# Use the official Alpine Linux Docker image
FROM alpine:latest

# Set the working directory
WORKDIR /smartgate

# Enable the testing repository
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories

# Install necessary packages
RUN apk update && \
    apk upgrade && \
    apk add bash git openssh sudo neofetch python && \
    rm -rf /var/cache/apk/*  # Clean up cache

# Install necessary python packages
RUN apk add py3-flask py3-authlib py3-requests py3-psycopg

# Create a non-root user 'developer'
RUN adduser -D developer

# Add 'developer' user to the 'wheel' group to allow sudo privileges
RUN adduser developer wheel

# Give the 'developer' user sudo privileges without password
RUN echo "developer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set proper permissions for the 'developer' user
RUN chown -R developer:developer /smartgate

# Switch to the 'developer' user
USER developer

# Expose both Flask (5000) & PostgreSQL (5432)
EXPOSE 5000 5432

# Keep the container running
CMD ["/bin/bash"]
