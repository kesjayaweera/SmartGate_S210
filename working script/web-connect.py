#!/usr/bin/env python3
"""
MQTT client for SmartGate that works with test.py
Receives MQTT commands and executes them using the existing test.py script
"""

import json
import socket
import time
import subprocess
import threading
from datetime import datetime

class SmartGateMQTTClient:
    """MQTT client for SmartGate that works with test.py"""
    
    def __init__(self, client_id="smartgate", broker_host="YOUR_EC2_PUBLIC_IP", broker_port=1883):
        self.client_id = client_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.socket = None
        self.connected = False
        self.test_script_path = "test.py"
    
    def connect(self):
        """Connect to MQTT broker and start listening for commands"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.broker_host, self.broker_port))
            self.connected = True
            print(f"[+] SmartGate MQTT client connected to {self.broker_host}:{self.broker_port}")
            
            # Subscribe to commands
            self._subscribe_to_commands()
            
            # Start listening for messages
            self._start_listening()
            
        except Exception as e:
            print(f"[-] Failed to connect: {e}")
            self.connected = False
    
    def _subscribe_to_commands(self):
        """Subscribe to command topic"""
        topic = "smartgate/gate1/commands"
        message = {
            "action": "subscribe",
            "topic": topic
        }
        
        try:
            self.socket.send(json.dumps(message).encode('utf-8'))
            print(f"[+] Subscribed to {topic}")
        except Exception as e:
            print(f"[-] Error subscribing to commands: {e}")
    
    def _start_listening(self):
        """Start listening for MQTT messages in a separate thread"""
        def listen():
            while self.connected:
                try:
                    data = self.socket.recv(1024)
                    if data:
                        message = json.loads(data.decode('utf-8'))
                        self._handle_message(message)
                except Exception as e:
                    if self.connected:
                        print(f"[-] Error receiving message: {e}")
                    break
        
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()
    
    def _handle_message(self, message):
        """Handle incoming MQTT message"""
        topic = message.get('topic', '')
        payload = message.get('payload', {})
        
        if 'smartgate/gate1/commands' in topic:
            command = payload.get('command')
            if command:
                print(f"[MQTT] Received command: {command}")
                self._execute_command(command)
    
    def _execute_command(self, command):
        """Execute command using test.py script"""
        try:
            if command == "OPEN_DOOR":
                print("[+] Executing: python3 test.py open")
                subprocess.run(["python3", self.test_script_path, "open"], check=True)
            elif command == "CLOSE_DOOR":
                print("[+] Executing: python3 test.py close")
                subprocess.run(["python3", self.test_script_path, "close"], check=True)
            elif command == "STOP_DOOR":
                print("[+] Executing: python3 test.py status (to stop)")
                subprocess.run(["python3", self.test_script_path, "status"], check=True)
            else:
                print(f"[-] Unknown command: {command}")
        except subprocess.CalledProcessError as e:
            print(f"[-] Error executing command: {e}")
        except Exception as e:
            print(f"[-] Error executing command: {e}")
    
    def publish_status(self):
        """Publish gate status"""
        try:
            # Get status from test.py
            result = subprocess.run(["python3", self.test_script_path, "status"], 
                                  capture_output=True, text=True, check=True)
            
            # Parse status from output
            status = "unknown"
            if "FULLY OPEN" in result.stdout:
                status = "open"
            elif "FULLY CLOSED" in result.stdout:
                status = "closed"
            elif "PARTIALLY OPEN" in result.stdout:
                status = "moving"
            
            topic = "smartgate/gate1/status"
            payload = {
                "gate_id": "gate1",
                "status": status,
                "timestamp": datetime.now().isoformat()
            }
            
            message = {
                "topic": topic,
                "payload": payload
            }
            
            self.socket.send(json.dumps(message).encode('utf-8'))
            print(f"[+] Published status: {status}")
            
        except Exception as e:
            print(f"[-] Error publishing status: {e}")
    
    def disconnect(self):
        """Disconnect from broker"""
        if self.socket:
            self.socket.close()
        self.connected = False
        print("[+] SmartGate MQTT client disconnected")

def main():
    """Main function - start MQTT client and keep running"""
    print("=" * 50)
    print("SmartGate MQTT Client")
    print("=" * 50)
    print("Connecting to MQTT broker and listening for commands...")
    print("Commands will be executed using test.py script")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    # Create MQTT client
    client = SmartGateMQTTClient()
    client.connect()
    
    if client.connected:
        try:
            # Keep running and publish status periodically
            while True:
                time.sleep(30)  # Publish status every 30 seconds
                client.publish_status()
        except KeyboardInterrupt:
            print("\n[+] Stopping MQTT client...")
            client.disconnect()
            print("[+] MQTT client stopped!")
    else:
        print("[-] Failed to connect to MQTT broker")

if __name__ == "__main__":
    main()
