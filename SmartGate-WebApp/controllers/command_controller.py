import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, List, Any
from enum import Enum
from dataclasses import dataclass
from controllers.db_controller import add_alert, get_db_connection
import json

class CommandType(Enum):
    EMERGENCY_STOP = "EMERGENCY_STOP"
    GATE_OPEN = "GATE_OPEN"
    GATE_CLOSE = "GATE_CLOSE"
    GATE_STOP = "GATE_STOP"
    SYSTEM_RESET = "SYSTEM_RESET"

class CommandStatus(Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

@dataclass
class Command:
    command_id: str
    command_type: CommandType
    gate_no: Optional[int]
    user_id: str
    timestamp: datetime
    status: CommandStatus
    task: Optional[asyncio.Task] = None
    priority: int = 1  # 1 = normal, 0 = emergency

class CommandManager:
    def __init__(self):
        self.command_queue: List[Command] = []
        self.current_operations: Dict[int, Command] = {}  # gate_no -> current command
        self.emergency_stop_active = False
        self.lock = asyncio.Lock()
        
    async def add_command(self, command_type: CommandType, gate_no: Optional[int], user_id: str, priority: int = 1) -> str:
        """Add a new command to the queue"""
        command_id = str(uuid.uuid4())
        command = Command(
            command_id=command_id,
            command_type=command_type,
            gate_no=gate_no,
            user_id=user_id,
            timestamp=datetime.now(),
            status=CommandStatus.PENDING,
            priority=priority
        )
        
        async with self.lock:
            if priority == 0:  # Emergency command
                # Emergency commands go to front of queue
                self.command_queue.insert(0, command)
            else:
                self.command_queue.append(command)
            
            # Log command to database
            await self._log_command_to_db(command)
            
        # Start processing if not already running
        asyncio.create_task(self._process_commands())
        
        return command_id
    
    async def _process_commands(self):
        """Process commands from the queue"""
        async with self.lock:
            if not self.command_queue:
                return
                
            # Get next command
            command = self.command_queue.pop(0)
            
            # Check if this is an emergency stop
            if command.command_type == CommandType.EMERGENCY_STOP:
                await self._execute_emergency_stop(command)
                return
            
            # Check if gate is already in operation
            if command.gate_no and command.gate_no in self.current_operations:
                # Cancel current operation
                current_cmd = self.current_operations[command.gate_no]
                if current_cmd.task and not current_cmd.task.done():
                    current_cmd.task.cancel()
                    current_cmd.status = CommandStatus.CANCELLED
                    await self._log_command_to_db(current_cmd)
            
            # Execute new command
            await self._execute_command(command)
    
    async def _execute_emergency_stop(self, command: Command):
        """Execute emergency stop - cancel all operations"""
        command.status = CommandStatus.EXECUTING
        await self._log_command_to_db(command)
        
        self.emergency_stop_active = True
        
        # Cancel all current operations
        for gate_no, current_cmd in list(self.current_operations.items()):
            if current_cmd.task and not current_cmd.task.done():
                current_cmd.task.cancel()
                current_cmd.status = CommandStatus.CANCELLED
                await self._log_command_to_db(current_cmd)
        
        # Clear current operations
        self.current_operations.clear()
        
        # Clear command queue (except emergency stops)
        self.command_queue = [cmd for cmd in self.command_queue if cmd.command_type == CommandType.EMERGENCY_STOP]
        
        # Add alert to database
        add_alert("Emergency stop activated - all gate operations halted", "CRITICAL")
        
        command.status = CommandStatus.COMPLETED
        await self._log_command_to_db(command)
        
        # Reset emergency stop flag after 5 seconds
        asyncio.create_task(self._reset_emergency_stop())
    
    async def _execute_command(self, command: Command):
        """Execute a gate command"""
        command.status = CommandStatus.EXECUTING
        await self._log_command_to_db(command)
        
        if command.gate_no:
            self.current_operations[command.gate_no] = command
        
        try:
            # Create task for the command execution
            if command.command_type == CommandType.GATE_OPEN:
                task = asyncio.create_task(self._open_gate(command))
            elif command.command_type == CommandType.GATE_CLOSE:
                task = asyncio.create_task(self._close_gate(command))
            elif command.command_type == CommandType.GATE_STOP:
                task = asyncio.create_task(self._stop_gate(command))
            elif command.command_type == CommandType.SYSTEM_RESET:
                task = asyncio.create_task(self._reset_system(command))
            else:
                raise ValueError(f"Unknown command type: {command.command_type}")
            
            command.task = task
            await task
            
            command.status = CommandStatus.COMPLETED
            await self._log_command_to_db(command)
            
        except asyncio.CancelledError:
            command.status = CommandStatus.CANCELLED
            await self._log_command_to_db(command)
            add_alert(f"Gate {command.gate_no} operation cancelled", "WARNING")
        except Exception as e:
            command.status = CommandStatus.FAILED
            await self._log_command_to_db(command)
            add_alert(f"Gate {command.gate_no} operation failed: {str(e)}", "ERROR")
        finally:
            if command.gate_no and command.gate_no in self.current_operations:
                del self.current_operations[command.gate_no]
            
            # Process next command
            asyncio.create_task(self._process_commands())
    
    async def _open_gate(self, command: Command):
        """Simulate gate opening operation"""
        if self.emergency_stop_active:
            raise asyncio.CancelledError("Emergency stop active")
        
        # Simulate gate opening time (5 seconds)
        for i in range(50):
            if self.emergency_stop_active:
                raise asyncio.CancelledError("Emergency stop active")
            await asyncio.sleep(0.1)
        
        # Update gate status in database
        from controllers.db_controller import update_gate_status
        update_gate_status(command.gate_no, "Open")
        
        add_alert(f"Gate {command.gate_no} opened successfully", "INFO")
    
    async def _close_gate(self, command: Command):
        """Simulate gate closing operation"""
        if self.emergency_stop_active:
            raise asyncio.CancelledError("Emergency stop active")
        
        # Simulate gate closing time (5 seconds)
        for i in range(50):
            if self.emergency_stop_active:
                raise asyncio.CancelledError("Emergency stop active")
            await asyncio.sleep(0.1)
        
        # Update gate status in database
        from controllers.db_controller import update_gate_status
        update_gate_status(command.gate_no, "Closed")
        
        add_alert(f"Gate {command.gate_no} closed successfully", "INFO")
    
    async def _stop_gate(self, command: Command):
        """Stop current gate operation"""
        if command.gate_no in self.current_operations:
            current_cmd = self.current_operations[command.gate_no]
            if current_cmd.task and not current_cmd.task.done():
                current_cmd.task.cancel()
                current_cmd.status = CommandStatus.CANCELLED
                await self._log_command_to_db(current_cmd)
        
        add_alert(f"Gate {command.gate_no} operation stopped", "WARNING")
    
    async def _reset_system(self, command: Command):
        """Reset all gates to closed state"""
        # Cancel all current operations
        for gate_no, current_cmd in list(self.current_operations.items()):
            if current_cmd.task and not current_cmd.task.done():
                current_cmd.task.cancel()
                current_cmd.status = CommandStatus.CANCELLED
                await self._log_command_to_db(current_cmd)
        
        # Close all gates
        from controllers.db_controller import update_gate_status
        for gate_no in range(1, 7):  # Assuming 6 gates
            update_gate_status(gate_no, "Closed")
        
        add_alert("System reset - all gates closed", "INFO")
    
    async def _reset_emergency_stop(self):
        """Reset emergency stop flag after delay"""
        await asyncio.sleep(5)
        self.emergency_stop_active = False
        add_alert("Emergency stop deactivated - normal operations resumed", "INFO")
    
    async def _log_command_to_db(self, command: Command):
        """Log command to database"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO command_logs (command_id, command_type, gate_no, user_id, status, timestamp, priority)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (command_id) 
                DO UPDATE SET status = %s, timestamp = %s
            """, (
                command.command_id,
                command.command_type.value,
                command.gate_no,
                command.user_id,
                command.status.value,
                command.timestamp,
                command.priority,
                command.status.value,
                command.timestamp
            ))
            
            conn.commit()
        except Exception as e:
            print(f"Error logging command to database: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def get_command_status(self, command_id: str) -> Optional[Command]:
        """Get status of a specific command"""
        # Check current operations
        for cmd in self.current_operations.values():
            if cmd.command_id == command_id:
                return cmd
        
        # Check queue
        for cmd in self.command_queue:
            if cmd.command_id == command_id:
                return cmd
        
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "emergency_stop_active": self.emergency_stop_active,
            "queue_length": len(self.command_queue),
            "active_operations": {
                gate_no: {
                    "command_id": cmd.command_id,
                    "command_type": cmd.command_type.value,
                    "user_id": cmd.user_id,
                    "status": cmd.status.value
                }
                for gate_no, cmd in self.current_operations.items()
            },
            "queued_commands": [
                {
                    "command_id": cmd.command_id,
                    "command_type": cmd.command_type.value,
                    "gate_no": cmd.gate_no,
                    "user_id": cmd.user_id,
                    "priority": cmd.priority
                }
                for cmd in self.command_queue
            ]
        }

# Global command manager instance
command_manager = CommandManager()

