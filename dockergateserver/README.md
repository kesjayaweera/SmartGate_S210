# SmartGate Bridge Docker Container

This Docker container acts as a bridge between your local SmartGate control interface and your hosted server. It solves the NAT traversal problem by maintaining an outbound connection to your server.

## Features

- **Outbound Connection**: Maintains persistent connection to hosted server
- **Local Interface**: Exposes port 8001 for local gate control
- **Automatic Reconnection**: Handles network interruptions gracefully
- **Heartbeat Monitoring**: Sends periodic status updates to server
- **Health Checks**: Built-in health monitoring and logging
- **Security**: API key authentication and secure communication

## Quick Start

1. **Configure the bridge**:
   ```bash
   cp env.example .env
   # Edit .env with your server details
   ```

2. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Check status**:
   ```bash
   curl http://localhost:8001/health
   ```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVER_HOST` | Hosted server IP address | `3.27.77.237` |
| `SERVER_PORT` | Server port | `8000` |
| `DEVICE_ID` | Unique device identifier | `gate-001` |
| `API_KEY` | Authentication key | `your-secret-api-key-here` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Configuration File

Edit `config.yaml` for advanced settings:

```yaml
server:
  host: "3.27.77.237"
  port: 8000
  endpoint: "/web-connect"
  reconnect_interval: 30
  heartbeat_interval: 60

gate:
  local_port: 8001
  interface_type: "http"

device:
  name: "SmartGate-Bridge"
  location: "Gate Location"
```

## API Endpoints

The bridge exposes the following local endpoints:

### Health Check
```bash
GET /health
```
Returns bridge status and connection information.

### Gate Status
```bash
GET /status
```
Returns current gate status and sensor readings.

### Gate Control
```bash
POST /control
Content-Type: application/json

{
  "command": "open|close|stop",
  "data": {}
}
```

### Device Registration
```bash
POST /register
```
Manually register device with server.

## Network Architecture

```
[SmartGate Hardware] <---> [Bridge Container:8001] <---> [Internet] <---> [Hosted Server:8000]
```

The bridge:
1. Listens on port 8001 for local gate commands
2. Maintains outbound connection to your server
3. Forwards commands and status updates
4. Handles automatic reconnection

## Monitoring

### Logs
```bash
# View container logs
docker-compose logs -f smartgate-bridge

# View application logs
tail -f logs/gate_bridge.log
```

### Health Monitoring
```bash
# Check container health
docker ps

# Check bridge health
curl http://localhost:8001/health
```

## Troubleshooting

### Connection Issues
1. Check server connectivity:
   ```bash
   ping 3.27.77.237
   ```

2. Verify server endpoint:
   ```bash
   curl http://3.27.77.237:8000/web-connect
   ```

3. Check container logs:
   ```bash
   docker-compose logs smartgate-bridge
   ```

### Port Conflicts
If port 8001 is already in use, modify `docker-compose.yml`:
```yaml
ports:
  - "8002:8001"  # Use different external port
```

### Permission Issues
Ensure the container has proper permissions:
```bash
sudo chown -R 1000:1000 logs/
```

## Security

- API key authentication for server communication
- Non-root user in container
- No new privileges security option
- Resource limits to prevent abuse
- Secure logging without sensitive data

## Development

### Building from Source
```bash
docker build -t smartgate-bridge .
```

### Running in Development Mode
```bash
# Set debug logging
export LOG_LEVEL=DEBUG

# Run with volume mount for live code changes
docker-compose -f docker-compose.dev.yml up
```

## Support

For issues or questions:
1. Check the logs first
2. Verify network connectivity
3. Ensure proper configuration
4. Review the troubleshooting section

