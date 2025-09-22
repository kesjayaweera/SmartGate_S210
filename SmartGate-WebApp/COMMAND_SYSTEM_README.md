# SmartGate Command System

This document describes the new command system that allows immediate interruption of current functions and execution of new commands.

## Overview

The command system provides:
- **Command Queue Management**: Orders and prioritizes commands
- **Function Interruption**: Immediately stops current operations
- **Emergency Stop**: Halts all operations system-wide
- **Real-time Status**: Live updates via WebSocket
- **Command Logging**: Full audit trail in database

## Architecture

### Core Components

1. **CommandManager** (`controllers/command_controller.py`)
   - Manages command queue and execution
   - Handles task cancellation and interruption
   - Provides system status information

2. **WebSocket Events** (`controllers/websocket_events.py`)
   - Real-time command execution
   - Status updates and notifications
   - Emergency stop handling

3. **REST API Endpoints** (`controllers/main_controller.py`)
   - Command submission
   - Status checking
   - System monitoring

4. **Frontend Integration** (`wwwroot/js/gate.js`, `frontend/test.html`)
   - Command execution interface
   - Real-time status display
   - Emergency stop controls

## Command Types

| Command Type | Description | Priority |
|--------------|-------------|----------|
| `EMERGENCY_STOP` | Halts all operations immediately | 0 (Highest) |
| `GATE_OPEN` | Opens specified gate | 1 (Normal) |
| `GATE_CLOSE` | Closes specified gate | 1 (Normal) |
| `GATE_STOP` | Stops current gate operation | 1 (Normal) |
| `SYSTEM_RESET` | Resets all gates to closed | 1 (Normal) |

## API Endpoints

### Command Execution
```http
POST /execute_command
Content-Type: application/json

{
    "command_type": "GATE_OPEN",
    "gate_no": 1,
    "priority": 1
}
```

### Emergency Stop
```http
POST /emergency_stop
```

### Command Status
```http
GET /command_status/{command_id}
```

### System Status
```http
GET /system_status
```

## WebSocket Events

### Client to Server
- `execute_command`: Submit new command
- `emergency_stop`: Activate emergency stop
- `get_command_status`: Check command status
- `get_system_status`: Get system overview

### Server to Client
- `command_submitted`: Command accepted
- `command_status`: Status update
- `emergency_stop_activated`: Emergency stop active
- `system_status`: System overview
- `error`: Error messages

## Database Schema

### Command Logs Table
```sql
CREATE TABLE command_logs (
    command_id VARCHAR(36) PRIMARY KEY,
    command_type VARCHAR(50) NOT NULL,
    gate_no INTEGER,
    user_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Gates Table Updates
```sql
ALTER TABLE gates ADD COLUMN current_operation VARCHAR(50);
ALTER TABLE gates ADD COLUMN operation_start_time TIMESTAMP;
```

## Usage Examples

### Basic Gate Control
```javascript
// Open gate 1
await executeCommand('GATE_OPEN', 1);

// Close gate 2
await executeCommand('GATE_CLOSE', 2);
```

### Emergency Stop
```javascript
// Activate emergency stop
await activateEmergencyStop();
```

### Command Status Monitoring
```javascript
// Monitor command execution
const commandId = await executeCommand('GATE_OPEN', 1);
const status = await getCommandStatus(commandId);
```

## Frontend Features

### Gates Page (`/gates`)
- **Emergency Stop Button**: Large red button at top
- **Operation Status**: Real-time indicators for each gate
- **Command Execution**: Integrated with existing open/close buttons
- **Visual Feedback**: Animated status indicators

### Test Control Panel (`/test`)
- **Command Queue Display**: Shows pending commands
- **Active Operations**: Lists currently executing commands
- **System Status**: Emergency stop status, queue length
- **Real-time Updates**: Auto-refreshes every 2 seconds

## Setup Instructions

### 1. Database Setup
```bash
# Run the database setup script
python setup_database.py
```

### 2. Environment Variables
Ensure `DATABASE_URL` is set in your environment.

### 3. Start the Application
```bash
python app.py
```

## Command Flow

1. **Command Submission**: User clicks button or sends API request
2. **Permission Check**: Verify user has required permissions
3. **Queue Addition**: Command added to queue (emergency commands go first)
4. **Interruption Check**: If gate is busy, current operation is cancelled
5. **Execution**: New command executes with real-time status updates
6. **Completion**: Command status updated, next command processed
7. **Logging**: All actions logged to database

## Safety Features

- **Emergency Stop**: Immediately halts all operations
- **Permission System**: Users must have appropriate permissions
- **Command Validation**: Invalid commands are rejected
- **Error Handling**: Graceful failure with user feedback
- **Audit Trail**: Complete command history in database

## Monitoring and Debugging

### System Status Endpoint
```http
GET /system_status
```

Returns:
```json
{
    "emergency_stop_active": false,
    "queue_length": 2,
    "active_operations": {
        "1": {
            "command_id": "uuid",
            "command_type": "GATE_OPEN",
            "user_id": "username",
            "status": "EXECUTING"
        }
    },
    "queued_commands": [...]
}
```

### Command Logs
All commands are logged with:
- Unique command ID
- Command type and parameters
- User who executed it
- Timestamp and status
- Priority level

## Error Handling

The system handles various error conditions:
- **Invalid Commands**: Rejected with error message
- **Permission Denied**: User feedback with reason
- **Database Errors**: Graceful degradation
- **Network Issues**: Retry mechanisms
- **Concurrent Access**: Thread-safe operations

## Performance Considerations

- **Async Operations**: Non-blocking command execution
- **Queue Management**: Efficient command ordering
- **Database Indexing**: Optimized queries for command logs
- **WebSocket Efficiency**: Minimal data transfer
- **Memory Management**: Automatic cleanup of completed commands

## Security

- **Authentication**: User session validation
- **Authorization**: Permission-based access control
- **Input Validation**: Command parameter sanitization
- **Audit Logging**: Complete action history
- **Rate Limiting**: Prevents command spam

## Troubleshooting

### Common Issues

1. **Commands Not Executing**
   - Check user permissions
   - Verify database connection
   - Check command queue status

2. **Emergency Stop Not Working**
   - Verify user is logged in
   - Check system status endpoint
   - Review error logs

3. **Status Not Updating**
   - Check WebSocket connection
   - Verify frontend JavaScript
   - Review browser console

### Debug Commands

```bash
# Check system status
curl http://localhost:8000/system_status

# Check command status
curl http://localhost:8000/command_status/{command_id}

# View recent commands in database
SELECT * FROM command_logs ORDER BY timestamp DESC LIMIT 10;
```

## Future Enhancements

- **Command Scheduling**: Execute commands at specific times
- **Batch Operations**: Execute multiple commands together
- **Command Templates**: Predefined command sequences
- **Advanced Monitoring**: Metrics and analytics
- **Mobile Interface**: Mobile-optimized controls

