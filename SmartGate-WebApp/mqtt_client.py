#!/usr/bin/env python3
"""
Simple MQTT Client for SmartGate WebApp
Connects to local MQTT broker
"""

import json
import socket
import threading
import time
from datetime import datetime
from typing import Dict, Any, Callable, Optional

class SimpleMQTTClient:
    """Simple MQTT client for WebApp"""
    
    def __init__(self, client_id="webapp", broker_host="localhost", broker_port=1883):
        self.client_id = client_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.socket = None
        self.connected = False
        self.subscriptions = []
        self.message_callbacks = {}
        
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
            
            print(f"[+] MQTT client {self.client_id} connected to {self.broker_host}:{self.broker_port}")
            
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
        print(f"[MQTT] Received on {topic}: {payload}")
        
        # Call registered callbacks
        for callback_topic, callback in self.message_callbacks.items():
            if callback_topic == topic or callback_topic.endswith('+'):
                try:
                    callback(topic, payload)
                except Exception as e:
                    print(f"[-] Error in message callback: {e}")
    
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
    
    def subscribe(self, topic: str, callback: Callable = None):
        """Subscribe to topic"""
        if topic not in self.subscriptions:
            self.subscriptions.append(topic)
            
            # Send subscription message to broker
            subscribe_message = {
                "action": "subscribe",
                "topic": topic
            }
            
            try:
                self.socket.send(json.dumps(subscribe_message).encode('utf-8'))
            except Exception as e:
                print(f"[-] Error subscribing to {topic}: {e}")
        
        if callback:
            self.message_callbacks[topic] = callback
        
        print(f"[MQTT] Subscribed to {topic}")
    
    def send_command(self, gate_id: str, command: str):
        """Send command to gate"""
        topic = f"smartgate/{gate_id}/commands"
        payload = {
            "command": command,
            "timestamp": datetime.now().isoformat(),
            "source": "webapp"
        }
        return self.publish(topic, payload)
    
    def disconnect(self):
        """Disconnect from broker"""
        self.connected = False
        if self.socket:
            self.socket.close()
        print(f"[+] MQTT client {self.client_id} disconnected")

# Global client instance
mqtt_client = None

def get_mqtt_client():
    """Get global MQTT client instance"""
    global mqtt_client
    if mqtt_client is None:
        mqtt_client = SimpleMQTTClient()
    return mqtt_client
