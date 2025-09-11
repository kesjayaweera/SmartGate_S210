#!/usr/bin/env python3
"""
Simple SmartGate Connection Test Script
- Connects to EC2 web app /test endpoint
- WebApp will wait 30 seconds then send gate open request back
- SmartGate HTTP server must be running to receive the gate open command
"""

import requests
import sys
import threading
import time
from door_control import DoorControl
from http_server import Initialize_Server, Fetch_Queued_Command

class SmartGateConnector:
    """Handles SmartGate connection to EC2 and command processing"""
    
    def __init__(self, ec2_ip, ec2_port=8000, local_port=8000):
        self.ec2_ip = ec2_ip
        self.ec2_port = ec2_port
        self.local_port = local_port
        self.ec2_base_url = f"http://{ec2_ip}:{ec2_port}"
        
        # Initialize door controller
        self.door_controller = DoorControl()
        
        # Initialize HTTP server
        server_config = {'port': local_port}
        self.web_server = Initialize_Server(server_config)
        
        # Set door controller reference for HTTP server
        from http_server import set_door_controller_reference
        set_door_controller_reference(self.door_controller)
        
        print(f"[+] SmartGate Connector initialized")
        print(f"[+] EC2 Target: {self.ec2_base_url}")
        print(f"[+] Local HTTP Server: localhost:{local_port}")
        print(f"[+] Door controller ready")
    
    def test_ec2_connection(self):
        """Test connection to EC2 web app - WebApp will handle gate opening"""
        url = f"{self.ec2_base_url}/test"
        print(f"[+] Testing connection to EC2: {url}")
        print(f"[+] WebApp will wait 30 seconds then send gate open request back to this device")
        
        try:
            # Send GET request to /test endpoint
            response = requests.get(url, timeout=10)
            
            # Check if we got HTTP 200 OK
            if response.status_code == 200:
                print(f"[+] SUCCESS: Connected to EC2 web app!")
                print(f"[+] Response: {response.text}")
                print(f"[+] WebApp will now wait 30 seconds and send gate open request to this device")
                return True
            else:
                print(f"[-] FAILED: EC2 returned HTTP {response.status_code}")
                print(f"[-] Response: {response.text}")
                return False
                
        except requests.exceptions.ConnectionError:
            print(f"[-] FAILED: Could not connect to EC2 at {url}")
            print(f"[-] Make sure the EC2 instance is running and accessible")
            return False
        except requests.exceptions.Timeout:
            print(f"[-] FAILED: EC2 connection timeout (10 seconds)")
            return False
        except Exception as e:
            print(f"[-] FAILED: Unexpected error: {str(e)}")
            return False
    
    def process_commands(self):
        """Continuously process commands from HTTP server queue"""
        print(f"[+] Starting command processor...")
        print(f"[+] Listening for commands from WebApp...")
        
        while True:
            try:
                # Check for commands from HTTP server queue
                command = Fetch_Queued_Command()
                if command:
                    print(f"[+] Received command: {command}")
                    
                    if command == 'OPEN_DOOR':
                        print(f"[+] Executing OPEN_DOOR command...")
                        self.door_controller.open_door()
                    elif command == 'CLOSE_DOOR':
                        print(f"[+] Executing CLOSE_DOOR command...")
                        self.door_controller.close_door()
                    elif command == 'STOP_DOOR':
                        print(f"[+] Executing STOP_DOOR command...")
                        self.door_controller.stop_door()
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
            except KeyboardInterrupt:
                print(f"\n[+] Command processor stopped by user")
                break
            except Exception as e:
                print(f"[-] Error processing commands: {str(e)}")
                time.sleep(1)

def main():
    """Main function"""
    print("=" * 60)
    print("SmartGate EC2 Connection Test")
    print("=" * 60)
    
    # Configuration
    EC2_IP = "192.168.0.1"  # Replace with actual EC2 IP
    EC2_PORT = 8000
    LOCAL_PORT = 8000
    
    # Initialize connector (starts HTTP server and door controller)
    connector = SmartGateConnector(EC2_IP, EC2_PORT, LOCAL_PORT)
    
    # Test EC2 connection
    print("\n[STEP 1] Testing EC2 Connection")
    print("-" * 40)
    if not connector.test_ec2_connection():
        print("\n[-] EC2 connection failed. Exiting.")
        sys.exit(1)
    
    # Start command processor (listens for commands from WebApp)
    print("\n[STEP 2] Start Command Processor")
    print("-" * 40)
    print("[+] Press Ctrl+C to stop the command processor")
    
    try:
        connector.process_commands()
    except KeyboardInterrupt:
        print("\n[+] Command processor stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
