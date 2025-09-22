#!/usr/bin/env python3
"""
Simple SmartGate Connection Test Script
- Connects to EC2 web app /test endpoint
- Serves control panel webpage for remote gate control
- SmartGate HTTP server must be running to receive commands

"""

import requests
import sys
import threading
import time
import subprocess
import os
import socket
from test import open_gate, close_gate, print_status
from http_server import Initialize_Server, Fetch_Queued_Command

class SmartGateConnector:
	"""Handles SmartGate connection to EC2 and command processing"""
	
	def __init__(self, ec2_ip, ec2_port=8000, local_port=8000, command_port=8001):
		self.ec2_ip = ec2_ip
		self.ec2_port = ec2_port
		self.local_port = local_port
		self.command_port = command_port
		self.ec2_base_url = "http://{}:{}".format(ec2_ip, ec2_port)
		
		# Get local IP address
		self.local_ip = self.get_local_ip()
		
		# Initialize HTTP server (for local use)
		server_config = {'port': local_port}
		self.web_server = Initialize_Server(server_config)
		
		# Initialize command server (for webapp commands)
		self.command_server = self.start_command_server()
		
		# Periodic check settings
		self.check_interval = 30  # Check every 30 seconds
		self.last_check_time = 0
		self.is_connected = False
		
		print("[+] SmartGate Connector initialized")
		print("[+] Local IP: {}".format(self.local_ip))
		print("[+] EC2 Target: {}".format(self.ec2_base_url))
		print("[+] Local HTTP Server: localhost:{}".format(local_port))
		print("[+] Command Server: 0.0.0.0:{} (accessible from webapp)".format(command_port))
		print("[+] Hall Effect sensor gate control ready")
		print("[+] Manual WiFi connection required - connect via GUI")
	
	def get_local_ip(self):
		"""Get the local IP address of this device"""
		try:
			# Connect to a remote address to determine local IP
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(("8.8.8.8", 80))
			local_ip = s.getsockname()[0]
			s.close()
			return local_ip
		except Exception as e:
			print("[-] Could not determine local IP: {}".format(str(e)))
			return "unknown"
	
	def start_command_server(self):
		"""Start a simple HTTP server to receive commands from webapp and run test.py functions directly"""
		import http.server
		import socketserver
		import json
		
		class CommandHandler(http.server.BaseHTTPRequestHandler):
			def __init__(self, *args, **kwargs):
				self.connector = kwargs.pop('connector')
				super().__init__(*args, **kwargs)
			
			def do_POST(self):
				content_length = int(self.headers['Content-Length'])
				post_data = self.rfile.read(content_length)
				
				print(f"[+] Command server received POST from: {self.client_address[0]}")
				print(f"[+] Request path: {self.path}")
				print(f"[+] Content length: {content_length}")
				print(f"[+] Raw POST data: {post_data.decode('utf-8')}")
				
				try:
					data = json.loads(post_data.decode('utf-8'))
					command = data.get('command')
					
					print(f"[+] Parsed command: {command}")
					print(f"[+] Full request data: {data}")
					
					if command in ['OPEN_DOOR', 'CLOSE_DOOR', 'STOP_DOOR']:
						print(f"[+] Valid command received: {command}")
						print(f"[+] Executing command directly using test.py functions...")
						
						# Execute command directly using test.py functions
						if command == 'OPEN_DOOR':
							print("[+] Calling open_gate() from test.py...")
							open_gate()
							print("[+] open_gate() completed")
						elif command == 'CLOSE_DOOR':
							print("[+] Calling close_gate() from test.py...")
							close_gate()
							print("[+] close_gate() completed")
						elif command == 'STOP_DOOR':
							print("[+] Calling stop gate function...")
							# Import io_control for immediate stop
							import io_control as io
							import Jetson.GPIO as GPIO
							io.set_val('IN3', False)
							io.set_val('IN4', False)
							io.all_pins_off()
							print("[+] Gate stopped immediately")
						
						self.send_response(200)
						self.send_header('Content-type', 'application/json')
						self.end_headers()
						response_data = {"status": "success", "message": f"Command {command} received and executed"}
						print(f"[+] Sending response: {response_data}")
						self.wfile.write(json.dumps(response_data).encode('utf-8'))
					else:
						print(f"[-] Invalid command received: {command}")
						self.send_response(400)
						self.send_header('Content-type', 'application/json')
						self.end_headers()
						self.wfile.write(json.dumps({"status": "error", "message": "Invalid command"}).encode('utf-8'))
				except json.JSONDecodeError:
					print(f"[-] JSON decode error")
					self.send_response(400)
					self.send_header('Content-type', 'application/json')
					self.end_headers()
					self.wfile.write(json.dumps({"status": "error", "message": "Invalid JSON"}).encode('utf-8'))
				except Exception as e:
					print(f"[-] Error executing command: {str(e)}")
					self.send_response(500)
					self.send_header('Content-type', 'application/json')
					self.end_headers()
					self.wfile.write(json.dumps({"status": "error", "message": f"Command execution failed: {str(e)}"}).encode('utf-8'))
			
			def log_message(self, format, *args):
				# Suppress default logging
				pass
		
		# Create handler with connector reference
		def handler(*args, **kwargs):
			kwargs['connector'] = self
			return CommandHandler(*args, **kwargs)
		
		# Start server
		try:
			server = socketserver.TCPServer(("0.0.0.0", self.command_port), handler)
			print(f"[+] Command server started on port {self.command_port}")
			print(f"[+] IP is still listening on port {self.command_port} at {self.local_ip}:{self.command_port} for POST requests")
			
			# Start server in a separate thread
			server_thread = threading.Thread(target=server.serve_forever, daemon=True)
			server_thread.start()
			print(f"[+] Command server thread started")
			
			return server
		except Exception as e:
			print(f"[-] Failed to start command server: {str(e)}")
			return None
	
	
	def test_ec2_connection(self):
		"""Test connection to EC2 web app - registers device for control panel"""
		url = "{}/web-connect".format(self.ec2_base_url)
		print("[+] Testing connection to EC2: {}".format(url))
		print("[+] Registering SmartGate device for remote control")
		print("[+] Sending GET request from IP: {} to IP: {}".format(self.local_ip, self.ec2_ip))
		print("[+] IP is still listening on port {} at {}:{} for POST requests".format(self.command_port, self.local_ip, self.command_port))
		print("[+] Sending GET request to EC2...")
		
		try:
			# Send GET request to /test endpoint
			response = requests.get(url, timeout=10)
			
			print("[+] EC2 Response received:")
			print("    Status Code: {}".format(response.status_code))
			print("    Response Headers: {}".format(dict(response.headers)))
			print("    Response Content: {}".format(response.text[:200] + "..." if len(response.text) > 200 else response.text))
			
			# Check if we got HTTP 200 OK
			if response.status_code == 200:
				print("[+] SUCCESS: Connected to EC2 web app!")
				print("[+] SmartGate device registered - control panel available at: {}".format(url))
				print("[+] IP is still listening on port {} at {}:{} for POST requests".format(self.command_port, self.local_ip, self.command_port))
				self.is_connected = True
				self.last_check_time = time.time()
				return True
			else:
				print("[-] FAILED: EC2 returned HTTP {}".format(response.status_code))
				self.is_connected = False
				return False
				
		except requests.exceptions.ConnectionError:
			print("[-] FAILED: Could not connect to EC2 at {}".format(url))
			print("[-] Make sure the EC2 instance is running and accessible")
			self.is_connected = False
			return False
		except requests.exceptions.Timeout:
			print("[-] FAILED: EC2 connection timeout (10 seconds)")
			self.is_connected = False
			return False
		except Exception as e:
			print("[-] FAILED: Unexpected error: {}".format(str(e)))
			self.is_connected = False
			return False
	
	def periodic_server_check(self):
		"""Periodically check with server to verify we're still the connected IP"""
		current_time = time.time()
		
		# Check if it's time for a periodic check
		if current_time - self.last_check_time >= self.check_interval:
			print("[+] Performing periodic server check...")
			print("[+] Checking if IP {} is still connected to server at {}".format(self.local_ip, self.ec2_ip))
			print("[+] IP is still listening on port {} at {}:{} for POST requests".format(self.command_port, self.local_ip, self.command_port))
			
			# Send a simple check request
			check_url = "{}/web-connect".format(self.ec2_base_url)
			try:
				response = requests.get(check_url, timeout=5)
				if response.status_code == 200:
					print("[+] Periodic check SUCCESS: Still connected as IP {}".format(self.local_ip))
					print("[+] IP is still listening on port {} at {}:{} for POST requests".format(self.command_port, self.local_ip, self.command_port))
					self.is_connected = True
					self.last_check_time = current_time
				else:
					print("[-] Periodic check FAILED: Server returned HTTP {}".format(response.status_code))
					self.is_connected = False
			except Exception as e:
				print("[-] Periodic check FAILED: {}".format(str(e)))
				self.is_connected = False
	
	def process_commands(self):
		"""Continuously process commands from HTTP server queue"""
		print("[+] Starting command processor...")
		print("[+] Listening for commands from WebApp...")
		
		while True:
			try:
				# Perform periodic server check
				self.periodic_server_check()
				
				# Check for commands from HTTP server queue
				command = Fetch_Queued_Command()
				if command:
					print("[+] Request to {} received".format(command.lower().replace('_', ' ')))
					print("[+] Command details: {}".format(command))
					
					if command == 'OPEN_DOOR':
						print("[+] Executing OPEN_DOOR command...")
						print("[+] Opening gate using Hall Effect sensors...")
						open_gate()
						print("[+] Gate opening completed")
					elif command == 'CLOSE_DOOR':
						print("[+] Executing CLOSE_DOOR command...")
						print("[+] Closing gate using Hall Effect sensors...")
						close_gate()
						print("[+] Gate closing completed")
					elif command == 'STOP_DOOR':
						print("[+] Executing STOP_DOOR command...")
						print("[+] Stopping gate...")
						# Import io_control for immediate stop
						import io_control as io
						import Jetson.GPIO as GPIO
						io.set_val('IN3', False)
						io.set_val('IN4', False)
						io.all_pins_off()
						print("[+] Gate stopped immediately")
				
				time.sleep(0.1)  # Small delay to prevent excessive CPU usage
				
			except KeyboardInterrupt:
				print("\n[+] Command processor stopped by user")
				break
			except Exception as e:
				print("[-] Error processing commands: {}".format(str(e)))
				time.sleep(1)
	

def main():
	"""Main function"""
	print("=" * 60)
	print("SmartGate EC2 Connection with Periodic Verification")
	print("=" * 60)
	
	# Configuration
	EC2_IP = "3.27.77.237"  # Replace with EC2 IP
	EC2_PORT = 8000
	LOCAL_PORT = 8000
	COMMAND_PORT = 8001  # Port for receiving commands from webapp
	
	# Initialize connector (starts HTTP server)
	connector = SmartGateConnector(EC2_IP, EC2_PORT, LOCAL_PORT, COMMAND_PORT)
	
	# Test EC2 connection
	print("\n[STEP 1] Test EC2 Connection")
	print("-" * 40)
	if not connector.test_ec2_connection():
		print("\n[-] EC2 connection failed. Exiting.")
		sys.exit(1)
	
	# Start command processor (listens for commands from WebApp)
	print("\n[STEP 2] Start Command Processor with Periodic Checks")
	print("-" * 40)
	print("[+] SmartGate device is now ready for remote control")
	print("[+] Access the control panel at: http://{}:{}/web-connect".format(EC2_IP, EC2_PORT))
	print("[+] Periodic server verification every {} seconds".format(connector.check_interval))
	print("[+] Press Ctrl+C to stop the command processor")
	
	try:
		connector.process_commands()
	except KeyboardInterrupt:
		print("\n[+] Command processor stopped by user")
		sys.exit(0)

if __name__ == "__main__":
	main()