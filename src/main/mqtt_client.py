#!/usr/bin/env python3
"""
Simple MQTT Client for SmartGate Device
Connects to WebApp's MQTT broker
"""

import json
import socket
import threading
import time
from datetime import datetime
from typing import Dict, Any, Callable, Optional

class SimpleGateMQTTClient:
    """Simple MQTT client for SmartGate device"""
    
    def __init__(self, gate_id="gate1", broker_host="YOUR_EC2_PUBLIC_IP", broker_port=1883):
        self.gate_id = gate_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.socket = None
        self.connected = False
        self.command_callbacks = []
        
        # Connect to broker
        self.connect()
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.broker_host, self.broker_port))
            self.connected = True
            
            # Start message listener
            listener_thread = threading.Thread(target=self._listen_for_messages)
            listener_thread.daemon = True
            listener_thread.start()
            
            # Subscribe to commands
            self._subscribe_to_commands()
            
            print(f"[+] Gate {self.gate_id} connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            
        except Exception as e:
            print(f"[-] Failed to connect to MQTT broker: {e}")
            self.connected = False
    
    def _listen_for_messages(self):
        """Listen for incoming messages"""
        while self.connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                
                message = json.loads(data.decode('utf-8'))
                topic = message.get('topic')
                payload = message.get('payload')
                
                if topic and payload:
                    self._handle_message(topic, payload)
                    
            except Exception as e:
                if self.connected:
                    print(f"[-] Error receiving message: {e}")
                break
    
    def _handle_message(self, topic: str, payload: Any):
        """Handle incoming message"""
        if f"smartgate/{self.gate_id}/commands" in topic:
            command = payload.get('command')
            if command:
                print(f"[MQTT] Received command: {command}")
                
                # Notify callbacks
                for callback in self.command_callbacks:
                    try:
                        callback(command, payload)
                    except Exception as e:
                        print(f"[-] Error in command callback: {e}")
    
    def _subscribe_to_commands(self):
        """Subscribe to command topic"""
        topic = f"smartgate/{self.gate_id}/commands"
        message = {
            "action": "subscribe",
            "topic": topic
        }
        
        try:
            self.socket.send(json.dumps(message).encode('utf-8'))
            print(f"[MQTT] Subscribed to {topic}")
        except Exception as e:
            print(f"[-] Error subscribing to commands: {e}")
    
    def publish(self, topic: str, payload: Any):
        """Publish message to topic"""
        if not self.connected:
            print("[-] Not connected to MQTT broker")
            return False
        
        try:
            message = {
                "topic": topic,
                "payload": payload,
                "timestamp": datetime.now().isoformat()
            }
            
            self.socket.send(json.dumps(message).encode('utf-8'))
            print(f"[MQTT] Published to {topic}: {payload}")
            return True
            
        except Exception as e:
            print(f"[-] Error publishing message: {e}")
            return False
    
    def publish_status(self, door_controller=None):
        """Publish gate status"""
        topic = f"smartgate/{self.gate_id}/status"
        
        # Get door status
        door_state = "unknown"
        
        if door_controller:
            if door_controller.is_door_fully_closed():
                door_state = "closed"
            elif door_controller.is_door_fully_open():
                door_state = "open"
            else:
                door_state = "moving"
        
        status = {
            "gate_id": self.gate_id,
            "status": door_state,
            "timestamp": datetime.now().isoformat()
        }
        
        return self.publish(topic, status)
    
    def add_command_callback(self, callback: Callable):
        """Add command callback"""
        self.command_callbacks.append(callback)
    
    def disconnect(self):
        """Disconnect from broker"""
        self.connected = False
        if self.socket:
            self.socket.close()
        print(f"[+] Gate {self.gate_id} disconnected from MQTT broker")

# Global client instance
mqtt_client = None

def get_mqtt_client(gate_id="gate1"):
    """Get global MQTT client instance"""
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = SimpleGateMQTTClient(gate_id=gate_id)
    return mqtt_client
