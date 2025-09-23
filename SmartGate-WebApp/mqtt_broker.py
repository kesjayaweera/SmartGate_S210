#!/usr/bin/env python3
"""
Simple MQTT Broker for SmartGate WebApp
Starts on container startup
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any
import socket
import threading
import time

class SimpleMQTTBroker:
    """Simple MQTT broker for SmartGate communication"""
    
    def __init__(self, host="0.0.0.0", port=1883):
        self.host = host
        self.port = port
        self.clients = {}  # client_id -> client_info
        self.subscriptions = {}  # topic -> [client_ids]
        self.messages = {}  # topic -> [messages]
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Start broker
        self.start_broker()
    
    def start_broker(self):
        """Start the MQTT broker"""
        self.logger.info(f"Starting MQTT broker on {self.host}:{self.port}")
        
        def handle_client(client_socket, addr):
            """Handle individual client connections"""
            client_id = f"client_{addr[0]}_{addr[1]}"
            self.clients[client_id] = {
                "socket": client_socket,
                "address": addr,
                "connected": True,
                "subscriptions": []
            }
            
            self.logger.info(f"Client {client_id} connected from {addr}")
            
            try:
                while True:
                    # Simple message handling (this is a basic implementation)
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Parse and handle MQTT message
                    self.handle_mqtt_message(client_id, data)
                    
            except Exception as e:
                self.logger.error(f"Error handling client {client_id}: {e}")
            finally:
                self.disconnect_client(client_id)
        
        def start_server():
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            
            self.logger.info(f"MQTT broker listening on {self.host}:{self.port}")
            
            while True:
                client_socket, addr = server_socket.accept()
                client_thread = threading.Thread(
                    target=handle_client, 
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()
        
        # Start server in background thread
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = True
        server_thread.start()
    
    def handle_mqtt_message(self, client_id: str, data: bytes):
        """Handle incoming MQTT message"""
        try:
            # Simple message parsing (basic implementation)
            message_str = data.decode('utf-8')
            message_data = json.loads(message_str)
            
            # Handle different message types
            if message_data.get('action') == 'subscribe':
                topic = message_data.get('topic')
                if topic:
                    if topic not in self.subscriptions:
                        self.subscriptions[topic] = []
                    if client_id not in self.subscriptions[topic]:
                        self.subscriptions[topic].append(client_id)
                    self.clients[client_id]['subscriptions'].append(topic)
                    self.logger.info(f"Client {client_id} subscribed to {topic}")
            
            elif message_data.get('topic') and message_data.get('payload'):
                topic = message_data.get('topic')
                payload = message_data.get('payload')
                
                self.logger.info(f"Received message on {topic} from {client_id}")
                
                # Store message
                if topic not in self.messages:
                    self.messages[topic] = []
                self.messages[topic].append({
                    "payload": payload,
                    "timestamp": datetime.now().isoformat(),
                    "client_id": client_id
                })
                
                # Forward to subscribed clients
                self.forward_message(topic, payload, client_id)
                
        except Exception as e:
            self.logger.error(f"Error handling message from {client_id}: {e}")
    
    def forward_message(self, topic: str, payload: Any, sender_id: str):
        """Forward message to subscribed clients"""
        # Check for wildcard subscriptions
        subscribed_clients = set()
        
        # Direct topic match
        if topic in self.subscriptions:
            subscribed_clients.update(self.subscriptions[topic])
        
        # Wildcard match (simple + wildcard)
        for sub_topic, clients in self.subscriptions.items():
            if sub_topic.endswith('+'):
                prefix = sub_topic[:-1]  # Remove the +
                if topic.startswith(prefix):
                    subscribed_clients.update(clients)
        
        # Send to subscribed clients
        for client_id in subscribed_clients:
            if client_id != sender_id and client_id in self.clients:
                try:
                    # Send message to client
                    message = {
                        "topic": topic,
                        "payload": payload,
                        "timestamp": datetime.now().isoformat()
                    }
                    self.clients[client_id]["socket"].send(json.dumps(message).encode('utf-8'))
                except Exception as e:
                    self.logger.error(f"Error forwarding message to {client_id}: {e}")
    
    def disconnect_client(self, client_id: str):
        """Disconnect a client"""
        if client_id in self.clients:
            client_info = self.clients[client_id]
            client_info["connected"] = False
            
            try:
                client_info["socket"].close()
            except:
                pass
            
            # Remove from subscriptions
            for topic, clients in self.subscriptions.items():
                if client_id in clients:
                    clients.remove(client_id)
            
            del self.clients[client_id]
            self.logger.info(f"Client {client_id} disconnected")

# Global broker instance
broker = None

def start_mqtt_broker():
    """Start the MQTT broker"""
    global broker
    if broker is None:
        broker = SimpleMQTTBroker()
        print("[+] MQTT broker started successfully")
    return broker

if __name__ == "__main__":
    start_mqtt_broker()
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[+] MQTT broker stopped")
