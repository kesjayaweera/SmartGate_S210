# MQTT Implementation for SmartGate

Gate (University) → Connects to → EC2 MQTT Broker (Port 1883) ← WebApp

**All HTTP-based direct communication has been removed** - the system now operates exclusively through MQTT messaging.

## ALTERNATE PORTS


at least according to chat

1. Port 8080 - Most likely to work
2. Port 443 - Almost never blocked
3. Port 80 - Rarely blocked
4. Port 8883 - MQTT standard secure
5. Port 3000 - Development friendly
6. Port 9001 - WebSocket friendly
7. Port 8083 - Alternative MQTT

These ports are much more likely to be open on university networks and corporate firewalls compared to the standard MQTT port 1883.

### 1. Configure EC2 IP Address

**Change**

```bash
# line 17
broker_host="YOUR_EC2_PUBLIC_IP"

```

## Step-by-Step

### Step 1: Start MQTT Broker (WebApp)

**What happens**: The WebApp automatically starts its own MQTT broker on port 1883 when it starts.

**Code**: `SmartGate-WebApp/controllers/main_controller.py`

```python
def initialize_mqtt():
    print("[+] Starting MQTT broker...")
    start_mqtt_broker()  # Starts broker on port 1883
    mqtt_client = get_mqtt_client()  # Connects WebApp to broker
    mqtt_client.subscribe("smartgate/+/status", on_gate_status)

# Called automatically when WebApp starts
initialize_mqtt()
```

### Step 2: WebApp Connects to Its Own Broker

**What happens**: The WebApp creates an MQTT client that connects to its local broker.

**Code**: `SmartGate-WebApp/mqtt_client.py`

```python
class SimpleMQTTClient:
    def __init__(self, broker_host="localhost", broker_port=1883):
        # Connects to local MQTT broker
        # Can send commands to gates
        # Receives status updates from gates
```

**Integration**: `SmartGate-WebApp/controllers/main_controller.py`

```python
# MQTT endpoints for sending commands
@root_router.post("/mqtt/send_command")
async def mqtt_send_command(request: Request):
    mqtt_client.send_command(gate_id, command)
```

### Step 3: Gate Device Connects to WebApp's Broker

**What happens**: The gate device connects to the WebApp's MQTT broker using the EC2's public IP.

**Code**: `src/main/mqtt_client.py`

```python
class SimpleGateMQTTClient:
    def __init__(self, gate_id="gate1", broker_host="your-ec2-ip", broker_port=1883):
        # Connects to WebApp's MQTT broker
        # Subscribes to command topics
        # Publishes status updates
```

**Configuration**: Hardcoded in the MQTT client files

**For Testing (Jetson):**

```python
# working script/web-connect.py line 17
def __init__(self, client_id="smartgate", broker_host="YOUR_EC2_PUBLIC_IP", broker_port=1883):
```

**For Production:**

```python
# src/main/mqtt_client.py line 17
def __init__(self, gate_id="gate1", broker_host="YOUR_EC2_PUBLIC_IP", broker_port=1883):
```

**To configure**: Replace `YOUR_EC2_PUBLIC_IP` with your actual EC2 public IP address in the appropriate file.

### Step 4: Send Commands via MQTT

**What happens**: WebApp sends commands through MQTT broker to the gate.

**Flow**:

1. User clicks button on test page
2. JavaScript calls `/mqtt/send_command` endpoint
3. WebApp MQTT client publishes to `smartgate/gate1/commands`
4. Gate receives command and processes it

**Code**: `SmartGate-WebApp/frontend/test.html`

```javascript
async function sendMQTTCommand(command) {
    const response = await fetch('/mqtt/send_command', {
        method: 'POST',
        body: JSON.stringify({
            gate_id: 'gate1',
            command: command
        })
    });
}
```

### Step 5: Gate Processes Commands

**What happens**: Gate receives MQTT commands and processes them directly.

**Code**: `src/main/mqtt_client.py`

```python
def _handle_message(self, topic: str, payload: Any):
    if f"smartgate/{self.gate_id}/commands" in topic:
        command = payload.get('command')
        if command:
            print(f"[MQTT] Received command: {command}")
            # Process command through existing gate logic
            for callback in self.command_callbacks:
                callback(command, payload)
```

**Note**: The `live_detection.py` script needs to be updated to integrate with the MQTT client for command processing.

### Step 6: Gate Sends Status Updates

**What happens**: Gate periodically publishes its status to the MQTT broker.

**Code**: `src/main/mqtt_client.py`

```python
def publish_status(self, door_controller=None):
    topic = f"smartgate/{self.gate_id}/status"
    status = {
        "gate_id": self.gate_id,
        "status": "closed",  # or "open", "moving"
        "timestamp": datetime.now().isoformat()
    }
    self.publish(topic, status)
```

### Step 7: WebApp Receives Status Updates

**What happens**: WebApp receives gate status and forwards to WebSocket clients.

**Code**: `SmartGate-WebApp/controllers/main_controller.py`

```python
def on_gate_status_received(gate_id: str, status_data: dict):
    asyncio.create_task(broadcast_data("gate_status", {
        "gate_id": gate_id,
        "status": status_data
    }))
```

## MQTT Topics

### Commands (WebApp → Gate)

**Topic**: `smartgate/gate1/commands`

```json
{
  "command": "OPEN_DOOR",
  "timestamp": "2024-01-01T12:00:00",
  "source": "webapp"
}
```

### Status (Gate → WebApp)

**Topic**: `smartgate/gate1/status`

```json
{
  "gate_id": "gate1",
  "status": "closed",
  "timestamp": "2024-01-01T12:00:00"
}
```

## How to Use

### 1. Start the System

```bash
cd SmartGate-WebApp
docker-compose up
```

This starts:

- WebApp on port 8000
- MQTT broker on port 1883

### 2. Configure Gate Device

**For Testing on Jetson:**
Edit `working script/web-connect.py` line 17:

```python
def __init__(self, client_id="smartgate", broker_host="YOUR_EC2_PUBLIC_IP", broker_port=1883):
```

Replace `YOUR_EC2_PUBLIC_IP` with your actual EC2 public IP address.

**For Production:**
Edit `src/main/mqtt_client.py` line 17:

```python
def __init__(self, gate_id="gate1", broker_host="YOUR_EC2_PUBLIC_IP", broker_port=1883):
```

Replace `YOUR_EC2_PUBLIC_IP` with your actual EC2 public IP address.

### 3. Run Gate Device

For testing on Jetson:

```bash
cd "working script"
python web-connect.py
```

For production:

```bash
cd src/main
python live_detection.py
```

### 4. Control Gate via Web Interface

Go to `http://your-ec2-ip:8000/web-connect`

```bash
cd working-scripts
python web-connect.py
```

## API Endpoints

### Send MQTT Command

```bash
POST /mqtt/send_command
{
  "gate_id": "gate1",
  "command": "OPEN_DOOR"
}
```

### Get Gate Status

```bash
GET /mqtt/gate_status/gate1
```

- n

## Troubleshooting

### Gate Cannot Connect to MQTT Broker

1. **Check EC2 Security Group**: Ensure port 1883 is open for inbound connections
2. **Verify IP Configuration**:
   - For testing: Check `broker_host="YOUR_EC2_PUBLIC_IP"` in `working script/web-connect.py` line 17
   - For production: Check `broker_host="YOUR_EC2_PUBLIC_IP"` in `src/main/mqtt_client.py` line 17
   - Replace `YOUR_EC2_PUBLIC_IP` with your actual EC2 public IP address
3. **Test Network Connection**: `telnet your-ec2-ip 1883` should connect successfully
4. **Check Broker Status**: `docker-compose logs smartgate-webapp` should show "[+] MQTT broker started successfully"
5. **Firewall Issues**: University network may block outbound connections to port 1883

### MQTT Commands Not Working

1. **Broker Running**: Verify MQTT broker is active with `docker-compose logs smartgate-webapp`
2. **Gate Subscription**: Check gate is subscribed to `smartgate/gate1/commands` topic
3. **Command Format**: Ensure commands are in correct JSON format with `command`, `timestamp`, `source` fields
4. **Test Connection**: Use `python "working script/web-connect.py"` to run the MQTT client that works with test.py
5. **Gate Integration**: Verify `live_detection.py` has MQTT client integrated for command processing

### Status Updates Not Appearing

1. **Gate Publishing**: Check gate is publishing to `smartgate/gate1/status` topic
2. **WebApp Subscription**: Verify WebApp MQTT client is subscribed to `smartgate/+/status`
3. **WebSocket Connection**: Check browser WebSocket connection in developer tools
4. **Status Format**: Ensure status messages include `gate_id`, `status`, `timestamp` fields
5. **Network Latency**: Status updates may have delays due to network conditions

### WebApp MQTT Issues

1. **Auto-Start Check**: Look for "[+] MQTT broker started successfully" in startup logs
2. **Client Connection**: Verify "[+] MQTT client connected and subscribed" message appears
3. **Port Conflicts**: Ensure port 1883 is not used by other services
4. **Restart WebApp**: `docker-compose restart smartgate-webapp` to reset MQTT components
5. **Container Logs**: Check `docker-compose logs -f smartgate-webapp` for real-time debugging

### Common Error Messages

- **"Connection refused"**: MQTT broker not running or port 1883 blocked
- **"No route to host"**: Incorrect EC2 IP address in gate configuration
- **"Connection timeout"**: Network connectivity issues or firewall blocking
- **"Topic not found"**: Gate not properly subscribed to command topics
- **"Invalid JSON"**: Malformed MQTT message payload

### Debug Commands

```bash
# Check WebApp MQTT broker status
docker-compose logs smartgate-webapp | grep MQTT

# Test MQTT connection from gate device
telnet your-ec2-ip 1883

# Monitor MQTT traffic (if broker supports it)
docker-compose exec smartgate-webapp netstat -tulpn | grep 1883

# Check gate MQTT client logs
python src/main/mqtt_client.py
```
