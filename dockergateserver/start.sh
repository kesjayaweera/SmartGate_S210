#!/bin/bash

# SmartGate Bridge Startup Script

set -e

echo "Starting SmartGate Bridge..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed."
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Set default environment variables if not set
export SERVER_HOST=${SERVER_HOST:-3.27.77.237}
export SERVER_PORT=${SERVER_PORT:-8000}
export DEVICE_ID=${DEVICE_ID:-gate-001}
export DEVICE_NAME=${DEVICE_NAME:-SmartGate-Bridge}
export API_KEY=${API_KEY:-your-secret-api-key-here}
export LOG_LEVEL=${LOG_LEVEL:-INFO}

echo "Configuration:"
echo "  Server: $SERVER_HOST:$SERVER_PORT"
echo "  Device ID: $DEVICE_ID"
echo "  Device Name: $DEVICE_NAME"
echo "  Log Level: $LOG_LEVEL"

# Build and start the container
echo "Building and starting SmartGate Bridge container..."
docker-compose up -d --build

# Wait for container to be healthy
echo "Waiting for container to be healthy..."
timeout=60
counter=0

while [ $counter -lt $timeout ]; do
    if docker-compose ps | grep -q "healthy"; then
        echo "Container is healthy!"
        break
    fi
    
    echo "Waiting for container health check... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "Warning: Container health check timed out"
fi

# Show container status
echo ""
echo "Container Status:"
docker-compose ps

# Show logs
echo ""
echo "Recent logs:"
docker-compose logs --tail=20 smartgate-bridge

echo ""
echo "SmartGate Bridge is running!"
echo "Local interface: http://localhost:8001"
echo "Health check: http://localhost:8001/health"
echo ""
echo "To view logs: docker-compose logs -f smartgate-bridge"
echo "To stop: docker-compose down"

