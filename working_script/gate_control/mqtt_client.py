#!/usr/bin/env python3
"""
SmartGate MQTT Client Module
Simple MQTT communication for commands, status, and debug logs
"""

import time
import json
import logging
from typing import Optional, Dict, List, Callable

logger = logging.getLogger(__name__)

class SmartGateMQTTClient:
    """
    Simple MQTT client for SmartGate system
    Handles commands, status, detections, and camera management
    """
    
    def __init__(self, broker_ip: str, broker_port: int = 1883, device_id: str = "smartgate_device_001"):
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.device_id = device_id
        self.client = None
        self.is_connected = False
        
        # MQTT topics
        self.command_topic = "smartgate/commands"
        self.status_topic = "smartgate/status"
        self.detection_topic = "smartgate/detections"
        self.last_animal_topic = "smartgate/last_animal"
        self.camera_status_topic = "smartgate/camera_status"
        self.system_status_topic = "smartgate/system_status"
        self.debug_logs_topic = "smartgate/debug_logs"
        
        # System state
        self.debug_messages = []
        self.max_debug_messages = 100
        
        # Debug logging for dashboard
        self.debug_logs = []
        self.max_debug_logs = 200
        
        # Callback functions for different message types
        self.command_callbacks = {}
        self.status_callbacks = {}
        self.camera_callbacks = {}
        
        logger.info(f"[MQTT] Initialized for broker {broker_ip}:{broker_port}")
    
    def add_debug_message(self, message: str, level: str = "INFO"):
        """Add debug message to list"""
        timestamp = time.time()
        debug_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        
        self.debug_messages.append(debug_entry)
        self.debug_logs.append(debug_entry)
        
        # Keep only recent messages
        if len(self.debug_messages) > self.max_debug_messages:
            self.debug_messages = self.debug_messages[-self.max_debug_messages:]
        
        if len(self.debug_logs) > self.max_debug_logs:
            self.debug_logs = self.debug_logs[-self.max_debug_logs:]
        
        # Also log to console
        logger.log(getattr(logging, level), f"[DEBUG] {message}")
        
        # Publish debug log to dashboard
        self._publish_debug_log(debug_entry)
    
    def register_command_callback(self, command: str, callback: Callable):
        """Register callback for specific command"""
        self.command_callbacks[command] = callback
        self.add_debug_message(f"Registered callback for command: {command}")
    
    def register_status_callback(self, callback: Callable):
        """Register callback for status requests"""
        self.status_callbacks['status_request'] = callback
        self.add_debug_message("Registered status request callback")
    
    def register_camera_callback(self, command: str, callback: Callable):
        """Register callback for camera commands"""
        self.camera_callbacks[command] = callback
        self.add_debug_message(f"Registered camera callback for: {command}")
    
    def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            import paho.mqtt.client as mqtt
            
            self.client = mqtt.Client()
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            
            self.add_debug_message(f"Connecting to MQTT broker {self.broker_ip}:{self.broker_port}")
            self.client.connect(self.broker_ip, self.broker_port, 60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.is_connected:
                self.add_debug_message("MQTT connection established", "SUCCESS")
                return True
            else:
                self.add_debug_message("MQTT connection timeout", "ERROR")
                return False
                
        except Exception as e:
            self.add_debug_message(f"MQTT connection error: {e}", "ERROR")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.is_connected = True
            self.add_debug_message("MQTT connected successfully")
            
            # Subscribe to topics
            topics = [
                self.command_topic,
                f"{self.status_topic}/+",
                f"{self.camera_status_topic}/+"
            ]
            
            for topic in topics:
                client.subscribe(topic)
                self.add_debug_message(f"Subscribed to {topic}")
        else:
            self.add_debug_message(f"MQTT connection failed with code {rc}", "ERROR")
    
    def _on_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            self.add_debug_message(f"Received MQTT message on {topic}: {payload[:100]}...")
            
            # Handle different message types
            if topic == self.command_topic:
                self._handle_command(payload)
            elif topic.startswith(self.status_topic):
                self._handle_status_request(topic, payload)
            elif topic.startswith(self.camera_status_topic):
                self._handle_camera_command(topic, payload)
                
        except Exception as e:
            self.add_debug_message(f"Error handling MQTT message: {e}", "ERROR")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.is_connected = False
        self.add_debug_message(f"MQTT disconnected (code: {rc})", "WARNING")
    
    def _handle_command(self, payload: str):
        """Handle command messages"""
        try:
            data = json.loads(payload)
            command = data.get('command')
            device_id = data.get('device_id')
            
            if device_id != self.device_id:
                return  # Not for this device
            
            self.add_debug_message(f"Processing command: {command}")
            
            # Check if we have a registered callback for this command
            if command in self.command_callbacks:
                try:
                    self.command_callbacks[command](data)
                except Exception as e:
                    self.add_debug_message(f"Error in command callback for {command}: {e}", "ERROR")
            else:
                self.add_debug_message(f"No callback registered for command: {command}", "WARNING")
                self._publish_status("error", f"Unknown command: {command}")
                
        except Exception as e:
            self.add_debug_message(f"Error handling command: {e}", "ERROR")
    
    def _handle_status_request(self, topic: str, payload: str):
        """Handle status request messages"""
        try:
            # Extract device ID from topic
            device_id = topic.split('/')[-1]
            if device_id == self.device_id:
                if 'status_request' in self.status_callbacks:
                    try:
                        self.status_callbacks['status_request']()
                    except Exception as e:
                        self.add_debug_message(f"Error in status callback: {e}", "ERROR")
        except Exception as e:
            self.add_debug_message(f"Error handling status request: {e}", "ERROR")
    
    def _handle_camera_command(self, topic: str, payload: str):
        """Handle camera-specific commands"""
        try:
            data = json.loads(payload)
            command = data.get('command')
            camera_id = data.get('camera_id')
            
            self.add_debug_message(f"Processing camera command: {command} for camera {camera_id}")
            
            # Check if we have a registered callback for this camera command
            if command in self.camera_callbacks:
                try:
                    self.camera_callbacks[command](data)
                except Exception as e:
                    self.add_debug_message(f"Error in camera callback for {command}: {e}", "ERROR")
            else:
                self.add_debug_message(f"No callback registered for camera command: {command}", "WARNING")
                
        except Exception as e:
            self.add_debug_message(f"Error handling camera command: {e}", "ERROR")
    
    def _publish_status(self, status: str, message: str):
        """Publish device status to MQTT broker"""
        if not self.is_connected:
            return
        
        status_data = {
            "device_id": self.device_id,
            "status": status,
            "message": message,
            "timestamp": time.time()
        }
        
        try:
            self.client.publish(self.status_topic, json.dumps(status_data))
            self.add_debug_message(f"Published status: {status} - {message}")
        except Exception as e:
            self.add_debug_message(f"Failed to publish status: {e}", "ERROR")
    
    def publish_system_status(self, status_data: Dict):
        """Publish system status to dashboard"""
        if not self.is_connected:
            return
        
        try:
            # Add device info and timestamp
            status_data.update({
                "device_id": self.device_id,
                "timestamp": time.time(),
                "mqtt_connected": self.is_connected
            })
            
            # Add debug messages
            status_data["debug_messages"] = self.debug_messages[-10:]  # Last 10 messages
            
            json_data = json.dumps(status_data, default=str)
            self.client.publish(self.system_status_topic, json_data)
            self.add_debug_message("System status sent to dashboard")
            
        except Exception as e:
            self.add_debug_message(f"Error sending system status: {e}", "ERROR")
    
    def publish_camera_status(self, camera_status: Dict):
        """Publish camera status update"""
        if not self.is_connected:
            return
        
        try:
            status_data = {
                "device_id": self.device_id,
                "camera_status": camera_status,
                "timestamp": time.time()
            }
            
            json_data = json.dumps(status_data, default=str)
            self.client.publish(self.camera_status_topic, json_data)
            self.add_debug_message("Camera status update sent")
            
        except Exception as e:
            self.add_debug_message(f"Error sending camera status: {e}", "ERROR")
    
    def publish_debug_logs(self):
        """Publish debug logs to dashboard"""
        if not self.is_connected:
            return
        
        try:
            logs_data = {
                "device_id": self.device_id,
                "debug_messages": self.debug_messages,
                "timestamp": time.time()
            }
            
            json_data = json.dumps(logs_data, default=str)
            self.client.publish(self.debug_logs_topic, json_data)
            self.add_debug_message("Debug logs sent to dashboard")
            
        except Exception as e:
            self.add_debug_message(f"Error sending debug logs: {e}", "ERROR")
    
    def publish_detection(self, detection_data: Dict):
        """Publish detection data"""
        if not self.is_connected:
            return
        
        try:
            detection_data.update({
                "device_id": self.device_id,
                "timestamp": time.time()
            })
            
            json_data = json.dumps(detection_data, default=str)
            self.client.publish(self.detection_topic, json_data)
            self.add_debug_message("Detection data published")
            
        except Exception as e:
            self.add_debug_message(f"Error publishing detection: {e}", "ERROR")
    
    def publish_last_animal(self, animal_data: Dict):
        """Publish last detected animal"""
        if not self.is_connected:
            return
        
        try:
            animal_data.update({
                "device_id": self.device_id,
                "timestamp": time.time()
            })
            
            json_data = json.dumps(animal_data, default=str)
            self.client.publish(self.last_animal_topic, json_data)
            self.add_debug_message("Last animal data published")
            
        except Exception as e:
            self.add_debug_message(f"Error publishing last animal: {e}", "ERROR")
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
            self.add_debug_message("MQTT disconnected")
    
    def get_debug_messages(self) -> List[Dict]:
        """Get debug messages"""
        return self.debug_messages.copy()
    
    def clear_debug_messages(self):
        """Clear debug messages"""
        self.debug_messages.clear()
        self.debug_logs.clear()
        self.add_debug_message("Debug messages cleared")
    
    def _publish_debug_log(self, debug_entry: Dict):
        """Publish individual debug log entry to dashboard"""
        if not self.is_connected:
            return
        
        try:
            log_data = {
                "device_id": self.device_id,
                "debug_log": debug_entry,
                "timestamp": time.time()
            }
            
            json_data = json.dumps(log_data, default=str)
            self.client.publish(self.debug_logs_topic, json_data)
            
        except Exception as e:
            logger.error(f"[MQTT] Error publishing debug log: {e}")
    
    def get_debug_logs(self) -> List[Dict]:
        """Get all debug logs"""
        return self.debug_logs.copy()
