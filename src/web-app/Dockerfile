# Use the official Alpine Linux Docker image
FROM alpine:latest

# Set the working directory
WORKDIR /webapp

# Install necessary packages
RUN apk update && \
    apk upgrade && \
    apk add bash git openssh sudo && \
    rm -rf /var/cache/apk/*  # Clean up cache

# Create a non-root user 'developer' and give them sudo privileges
RUN adduser -D developer && \
    echo "developer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set proper permissions for the developer user
RUN chown -R developer:developer /webapp

# Switch to the 'developer' user
USER developer

# Clone the repo inside the container
RUN git clone https://github.com/ChristopherLaff/SmartGate.git /webapp

# Expose both Flask (5000) & PostgreSQL (5432)
EXPOSE 5000 5432

# Keep the container running
CMD ["/bin/bash"]
