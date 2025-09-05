# SmartGate Web Application - Standalone Deployment

This is the standalone SmartGate Web Application that can be deployed independently on any server or cloud instance (e.g., EC2).

## Overview

The SmartGate Web Application provides a web-based interface for monitoring and controlling SmartGate devices remotely. It includes:

- Web dashboard for gate monitoring
- User management system
- Real-time status updates
- Database storage for gate data and user information
- RESTful API for gate communication

## Architecture

- **Web Application**: FastAPI-based Python application
- **Database**: PostgreSQL for data persistence
- **Frontend**: HTML/CSS/JavaScript with Bootstrap
- **Containerization**: Docker and Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Port 8000 and 5432 available on the host

### Deployment

1. **Clone or copy this directory to your server**

2. **Start the application**:
   ```bash
   docker-compose up -d
   ```

3. **Access the web application**:
   - Open your browser and navigate to `http://your-server-ip:8000`
   - The application will be available on port 8000

### Configuration

The application uses the following default configuration:

- **Web App Port**: 8000
- **Database Port**: 5432
- **Database**: PostgreSQL 13
- **Database Name**: smartgatedb
- **Database User**: admin
- **Database Password**: smartgate

## Services

### smartgate-webapp
- **Container Name**: smartgate-webapp
- **Port**: 8000
- **Environment**: Production
- **Restart Policy**: unless-stopped

### postgres
- **Container Name**: smartgate-postgres
- **Port**: 5432
- **Database**: smartgatedb
- **Restart Policy**: unless-stopped

## Health Checks

Both services include health checks:
- **Web App**: HTTP health check on `/health` endpoint
- **Database**: PostgreSQL readiness check

## Data Persistence

Database data is persisted in the `smartgate-webapp-data` Docker volume.

## Security Notes

- The web application runs as a non-root user inside the container
- Database credentials are set via environment variables
- Consider changing default passwords in production

## Monitoring

Check container status:
```bash
docker-compose ps
```

View logs:
```bash
docker-compose logs -f
```

## Stopping the Application

```bash
docker-compose down
```

To also remove volumes (WARNING: This will delete all data):
```bash
docker-compose down -v
```

## API Endpoints

The web application provides REST API endpoints for gate communication:

- `GET /health` - Health check
- `POST /api/gates/register` - Register a new gate
- `POST /api/gates/{gate_id}/status` - Update gate status
- `POST /api/gates/{gate_id}/stream` - Receive camera frames
- `POST /api/gates/{gate_id}/action_result` - Receive action results

## Support

For issues or questions, refer to the main SmartGate documentation or contact the development team.

