@echo off
REM SmartGate Bridge Startup Script for Windows

echo Starting SmartGate Bridge...

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running. Please start Docker first.
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: docker-compose is not installed.
    exit /b 1
)

REM Create logs directory if it doesn't exist
if not exist logs mkdir logs

REM Set default environment variables if not set
if not defined SERVER_HOST set SERVER_HOST=3.27.77.237
if not defined SERVER_PORT set SERVER_PORT=8000
if not defined DEVICE_ID set DEVICE_ID=gate-001
if not defined DEVICE_NAME set DEVICE_NAME=SmartGate-Bridge
if not defined API_KEY set API_KEY=your-secret-api-key-here
if not defined LOG_LEVEL set LOG_LEVEL=INFO

echo Configuration:
echo   Server: %SERVER_HOST%:%SERVER_PORT%
echo   Device ID: %DEVICE_ID%
echo   Device Name: %DEVICE_NAME%
echo   Log Level: %LOG_LEVEL%

REM Build and start the container
echo Building and starting SmartGate Bridge container...
docker-compose up -d --build

REM Wait for container to start
echo Waiting for container to start...
timeout /t 10 /nobreak >nul

REM Show container status
echo.
echo Container Status:
docker-compose ps

REM Show logs
echo.
echo Recent logs:
docker-compose logs --tail=20 smartgate-bridge

echo.
echo SmartGate Bridge is running!
echo Local interface: http://localhost:8001
echo Health check: http://localhost:8001/health
echo.
echo To view logs: docker-compose logs -f smartgate-bridge
echo To stop: docker-compose down

pause

