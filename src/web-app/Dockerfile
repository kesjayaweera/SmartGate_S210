# Use the official Alpine Linux Docker image
FROM alpine:latest

# Set the working directory
WORKDIR /webapp

# Update the system
RUN apk update && \
    apk upgrade && \
    rm -rf /var/cache/apk/*  # Clean up cache

# Expose both Flask (5000) & PostgreSQL (5432)
EXPOSE 5000 5432

# Keep the container running
CMD ["/bin/sh"]

