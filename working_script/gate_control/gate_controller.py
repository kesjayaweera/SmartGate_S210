#!/usr/bin/env python3
"""
SmartGate Gate Control Module
Simple gate operations using existing test.py functions
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class GateController:
    """
    Simple gate control handler
    Uses existing test.py functions for gate operations
    """
    
    def __init__(self, mqtt_client=None):
        self.mqtt_client = mqtt_client
        self.gate_control_available = False
        self.gate_status = "unknown"
        
        # Try to load gate control functions
        self._load_gate_functions()
    
    def _load_gate_functions(self):
        """Load gate control functions from test.py"""
        try:
            # Import gate control functions from existing test.py
            from test import open_gate, close_gate, print_status
            import io_control as io
            
            self.open_gate_func = open_gate
            self.close_gate_func = close_gate
            self.print_status_func = print_status
            self.io_control = io
            
            self.gate_control_available = True
            logger.info("[GATE] Gate control loaded successfully")
            
            if self.mqtt_client:
                self.mqtt_client.add_debug_message("Gate control loaded successfully")
                
        except ImportError as e:
            logger.warning(f"[GATE] Gate control not available: {e}")
            self.gate_control_available = False
            
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(f"Gate control not available: {e}", "WARNING")
    
    def open_gate(self) -> Dict[str, Any]:
        """Open gate command - simple wrapper around test.py function"""
        if not self.gate_control_available:
            error_msg = "Gate control not available"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            return {"success": False, "message": error_msg, "error": error_msg}
        
        try:
            if self.mqtt_client:
                self.mqtt_client.add_debug_message("Opening gate...")
            
            # Call the existing open_gate function from test.py
            self.open_gate_func()
            self.gate_status = "opening"
            
            success_msg = "Gate opening command executed"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(success_msg, "SUCCESS")
            
            logger.info("[GATE] Gate opening command executed")
            return {"success": True, "message": success_msg, "error": None}
            
        except Exception as e:
            error_msg = f"Error opening gate: {e}"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            logger.error(f"[GATE] {error_msg}")
            return {"success": False, "message": error_msg, "error": str(e)}
    
    def close_gate(self) -> Dict[str, Any]:
        """Close gate command - simple wrapper around test.py function"""
        if not self.gate_control_available:
            error_msg = "Gate control not available"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            return {"success": False, "message": error_msg, "error": error_msg}
        
        try:
            if self.mqtt_client:
                self.mqtt_client.add_debug_message("Closing gate...")
            
            # Call the existing close_gate function from test.py
            self.close_gate_func()
            self.gate_status = "closing"
            
            success_msg = "Gate closing command executed"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(success_msg, "SUCCESS")
            
            logger.info("[GATE] Gate closing command executed")
            return {"success": True, "message": success_msg, "error": None}
            
        except Exception as e:
            error_msg = f"Error closing gate: {e}"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            logger.error(f"[GATE] {error_msg}")
            return {"success": False, "message": error_msg, "error": str(e)}
    
    def stop_gate(self) -> Dict[str, Any]:
        """Stop gate command - stops motor immediately"""
        if not self.gate_control_available:
            error_msg = "Gate control not available"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            return {"success": False, "message": error_msg, "error": error_msg}
        
        try:
            if self.mqtt_client:
                self.mqtt_client.add_debug_message("Stopping gate...")
            
            # Stop gate motor by setting control pins to False
            self.io_control.set_val('IN3', False)  # Close pin off
            self.io_control.set_val('IN4', False)  # Open pin off
            self.io_control.all_pins_off()         # Ensure all pins are off
            
            self.gate_status = "stopped"
            
            success_msg = "Gate stop command executed"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(success_msg, "SUCCESS")
            
            logger.info("[GATE] Gate stop command executed")
            return {"success": True, "message": success_msg, "error": None}
            
        except Exception as e:
            error_msg = f"Error stopping gate: {e}"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            logger.error(f"[GATE] {error_msg}")
            return {"success": False, "message": error_msg, "error": str(e)}
    
    def get_gate_status(self) -> Dict[str, Any]:
        """Get gate status - checks Hall Effect sensors for position"""
        if not self.gate_control_available:
            error_msg = "Gate control not available"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            return {"success": False, "message": error_msg, "error": error_msg, "status": "unknown"}
        
        try:
            if self.mqtt_client:
                self.mqtt_client.add_debug_message("Getting gate status...")
            
            # Check Hall Effect sensors to determine gate position
            # OPEN sensor: 0 = gate is open, 1 = gate is not open
            # CLOSE sensor: 0 = gate is not closed, 1 = gate is closed
            is_open = self.io_control.get_val('OPEN') == 0 and self.io_control.get_val('CLOSE') == 1
            is_closed = self.io_control.get_val('OPEN') == 1 and self.io_control.get_val('CLOSE') == 0
            
            if is_open:
                self.gate_status = "fully_open"
            elif is_closed:
                self.gate_status = "fully_closed"
            else:
                self.gate_status = "in_motion"  # Gate is between positions
            
            success_msg = f"Gate status: {self.gate_status}"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(success_msg, "INFO")
            
            logger.info(f"[GATE] {success_msg}")
            return {"success": True, "message": success_msg, "error": None, "status": self.gate_status}
            
        except Exception as e:
            error_msg = f"Error getting gate status: {e}"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            logger.error(f"[GATE] {error_msg}")
            return {"success": False, "message": error_msg, "error": str(e), "status": "unknown"}
    
    def is_available(self) -> bool:
        """Check if gate control is available"""
        return self.gate_control_available
    
    def handle_mqtt_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle MQTT gate commands - simple command router"""
        if params is None:
            params = {}
        
        command = command.upper()
        
        # Route commands to appropriate methods
        if command == "OPEN_GATE":
            return self.open_gate()
        elif command == "CLOSE_GATE":
            return self.close_gate()
        elif command == "STOP_GATE":
            return self.stop_gate()
        elif command == "GET_STATUS":
            return self.get_gate_status()
        else:
            error_msg = f"Unknown gate command: {command}"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            
            return {"success": False, "message": error_msg, "error": error_msg}

