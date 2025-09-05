# SmartGate Web Application - Standalone Docker Container
# Use the official Python Docker image (OS: Debian)
FROM python:3.9.22-bookworm

# Set metadata
LABEL maintainer="SmartGate Team"
LABEL description="SmartGate Web Application - Standalone Deployment"
LABEL version="1.0"

# Set the working directory inside the container
WORKDIR /SmartGate-WebApp

# Copy requirements first for better Docker layer caching
COPY requirements.txt /SmartGate-WebApp/

# Update, upgrade and install system dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
        curl \
        sudo \
        nano \
        libdbus-1-dev \
        neofetch \
        postgresql-client \
        openssh-client \
        neovim && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install the required Python packages from the requirements.txt file
RUN pip install --no-cache-dir -r /SmartGate-WebApp/requirements.txt

# Copy the rest of the application code to the container
COPY . /SmartGate-WebApp/

# Create a non-root user for security
RUN useradd -m -s /bin/bash smartgate && \
    chown -R smartgate:smartgate /SmartGate-WebApp

# Switch to non-root user
USER smartgate

# Expose the web application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the web application
ENTRYPOINT ["python", "app.py"]
