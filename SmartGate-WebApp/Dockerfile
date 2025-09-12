# SmartGate Web Application - Standalone Docker Container
# Use the official Python Docker image (OS: Debian)
FROM python:3.9.22-bookworm

# Set metadata
LABEL maintainer="SmartGate Team"
LABEL description="SmartGate Web Application - Standalone Deployment"
LABEL version="1.0"

# Set the working directory inside the container
WORKDIR /SmartGate-WebApp

# Update package lists and install system dependencies
# Split into separate RUN commands for better error handling
RUN apt-get update

RUN apt-get install -y --no-install-recommends \
    curl \
    sudo \
    nano \
    libdbus-1-dev \
    libpq-dev \
    postgresql-client \
    openssh-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install the required Python packages directly
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        authlib \
        dbus-python \
        python-dotenv \
        fastapi \
        flask \
        h11 \
        httpx \
        jinja2 \
        psycopg \
        requests \
        starlette \
        uvicorn \
        websocket-client \
        websockets \
        pandas \
        matplotlib \
        plotly

# Copy the application code to the container
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
