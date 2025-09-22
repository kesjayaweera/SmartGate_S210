from typing import Callable, Dict, Awaitable, Union
from fastapi import WebSocket
from controllers.main_controller import broadcast_user_overview, websocket_state, fetch_user_data
from controllers.command_controller import command_manager, CommandType

event_registry: Dict[str, Callable[[WebSocket, dict], Awaitable[Union[dict, None]]]] = {}

def register_event(event_name: str):
    def decorator(func: Callable[[WebSocket, dict], Awaitable[Union[dict, None]]]):
        event_registry[event_name] = func
        return func
    return decorator

@register_event("init")
async def init_event(websocket: WebSocket, data: dict):
    username = data.get("username")
    if username:
        websocket_state[websocket] = {"username": username, "data": None}
    return None

@register_event("user_overview")
async def user_overview_event(websocket: WebSocket, data: dict):
    user_data = fetch_user_data()  # Use the refactored function
    return {"event": "user_overview", "data": user_data}

@register_event("change_role")
async def change_role_event(websocket: WebSocket, data: dict):
    from controllers.db_controller import change_role  # Local import to avoid circular imports
    username = data.get("username")
    new_role = data.get("role")
    if username and new_role:
        change_role(username, new_role)
        await broadcast_user_overview()
    return None

@register_event("alert_data")
async def alert_data_event(websocket: WebSocket, data: dict):
    from controllers.main_controller import fetch_alerts_data  # Local import to avoid circular imports
    alert_data = fetch_alerts_data()
    return {"event": "alert_data", "data": alert_data}

@register_event("execute_command")
async def execute_command_event(websocket: WebSocket, data: dict):
    """Handle command execution requests"""
    command_type = data.get("command_type")
    gate_no = data.get("gate_no")
    user_id = data.get("user_id")
    priority = data.get("priority", 1)
    
    if not command_type or not user_id:
        return {"event": "error", "message": "Missing required fields: command_type, user_id"}
    
    try:
        # Convert string to CommandType enum
        cmd_type = CommandType(command_type)
        command_id = await command_manager.add_command(cmd_type, gate_no, user_id, priority)
        
        return {
            "event": "command_submitted",
            "data": {
                "command_id": command_id,
                "command_type": command_type,
                "gate_no": gate_no,
                "status": "PENDING"
            }
        }
    except ValueError:
        return {"event": "error", "message": f"Invalid command type: {command_type}"}
    except Exception as e:
        return {"event": "error", "message": f"Failed to execute command: {str(e)}"}

@register_event("get_command_status")
async def get_command_status_event(websocket: WebSocket, data: dict):
    """Get status of a specific command"""
    command_id = data.get("command_id")
    
    if not command_id:
        return {"event": "error", "message": "Missing command_id"}
    
    command = command_manager.get_command_status(command_id)
    if command:
        return {
            "event": "command_status",
            "data": {
                "command_id": command.command_id,
                "command_type": command.command_type.value,
                "gate_no": command.gate_no,
                "status": command.status.value,
                "timestamp": command.timestamp.isoformat()
            }
        }
    else:
        return {"event": "error", "message": "Command not found"}

@register_event("get_system_status")
async def get_system_status_event(websocket: WebSocket, data: dict):
    """Get current system status"""
    status = command_manager.get_system_status()
    return {"event": "system_status", "data": status}

@register_event("emergency_stop")
async def emergency_stop_event(websocket: WebSocket, data: dict):
    """Handle emergency stop requests"""
    user_id = data.get("user_id")
    
    if not user_id:
        return {"event": "error", "message": "Missing user_id"}
    
    try:
        command_id = await command_manager.add_command(CommandType.EMERGENCY_STOP, None, user_id, priority=0)
        
        return {
            "event": "emergency_stop_activated",
            "data": {
                "command_id": command_id,
                "message": "Emergency stop activated - all operations halted"
            }
        }
    except Exception as e:
        return {"event": "error", "message": f"Failed to activate emergency stop: {str(e)}"}
