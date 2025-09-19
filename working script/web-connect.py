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
from doorTest import openDoor, closeDoor, initDoor
from http_server import Initialize_Server, Fetch_Queued_Command

class SmartGateConnector:
	"""Handles SmartGate connection to EC2 and command processing"""
	
	def __init__(self, ec2_ip, ec2_port=8000, local_port=8000):
		self.ec2_ip = ec2_ip
		self.ec2_port = ec2_port
		self.local_port = local_port
		self.ec2_base_url = "http://{}:{}".format(ec2_ip, ec2_port)
		
		# Initialize door functions (from doorTest.py)
		initDoor()
		
		# Initialize HTTP server
		server_config = {'port': local_port}
		self.web_server = Initialize_Server(server_config)
		
		print("[+] SmartGate Connector initialized")
		print("[+] EC2 Target: {}".format(self.ec2_base_url))
		print("[+] Local HTTP Server: localhost:{}".format(local_port))
		print("[+] Door functions ready (openDoor, closeDoor)")
		print("[+] Manual WiFi connection required - connect via GUI")
	
	def check_internet_connection(self):
		"""Check if internet connection is available"""
		print("[+] Checking internet connection...")
		
		try:
			# Try to ping Google DNS
			result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
								 capture_output=True, text=True, timeout=10)
			if result.returncode == 0:
				print("[+] Internet connection available")
				return True
			else:
				print("[-] No internet connection")
				return False
		except Exception as e:
			print("[-] Internet check failed: {}".format(str(e)))
			return False
	
	def test_ec2_connection(self):
		"""Test connection to EC2 web app - registers device for control panel"""
		url = "{}/test".format(self.ec2_base_url)
		print("[+] Testing connection to EC2: {}".format(url))
		print("[+] Registering SmartGate device for remote control")
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
				return True
			else:
				print("[-] FAILED: EC2 returned HTTP {}".format(response.status_code))
				return False
				
		except requests.exceptions.ConnectionError:
			print("[-] FAILED: Could not connect to EC2 at {}".format(url))
			print("[-] Make sure the EC2 instance is running and accessible")
			return False
		except requests.exceptions.Timeout:
			print("[-] FAILED: EC2 connection timeout (10 seconds)")
			return False
		except Exception as e:
			print("[-] FAILED: Unexpected error: {}".format(str(e)))
			return False
	
	def process_commands(self):
		"""Continuously process commands from HTTP server queue"""
		print("[+] Starting command processor...")
		print("[+] Listening for commands from WebApp...")
		
		while True:
			try:
				# Check for commands from HTTP server queue
				command = Fetch_Queued_Command()
				if command:
					print("[+] Request to {} received".format(command.lower().replace('_', ' ')))
					print("[+] Command details: {}".format(command))
					
					if command == 'OPEN_DOOR':
						print("[+] Executing OPEN_DOOR command...")
						print("[+] Opening gate...")
						openDoor()
						print("[+] Gate opening started")
					elif command == 'CLOSE_DOOR':
						print("[+] Executing CLOSE_DOOR command...")
						print("[+] Closing gate...")
						closeDoor()
						print("[+] Gate closing started")
					elif command == 'STOP_DOOR':
						print("[+] Executing STOP_DOOR command...")
						print("[+] Stopping gate...")
						# Import ioControl for cleanup
						import ioControl as io
						io.allPinsOff()
						print("[+] Gate stopped")
				
				time.sleep(0.1)  # Small delay to prevent excessive CPU usage
				
			except KeyboardInterrupt:
				print("\n[+] Command processor stopped by user")
				break
			except Exception as e:
				print("[-] Error processing commands: {}".format(str(e)))
				time.sleep(1)
	
	def cleanup(self):
		"""Cleanup GPIO and pins when exiting"""
		print("[+] Cleaning up...")
		import ioControl as io
		import Jetson.GPIO as GPIO
		io.allPinsOff()
		GPIO.cleanup()
		print("[+] Cleanup complete")

def main():
	"""Main function"""
	print("=" * 60)
	print("SmartGate EC2 Connection Test")
	print("=" * 60)
	
	# Configuration
	EC2_IP = "3.27.77.237"  # Replace with EC2 IP
	EC2_PORT = 8000
	LOCAL_PORT = 8000
	
	# Initialize connector (starts HTTP server and door controller)
	connector = SmartGateConnector(EC2_IP, EC2_PORT, LOCAL_PORT)
	
	# Check internet connection
	print("\n[STEP 1] Check Internet Connection")
	print("-" * 40)
	print("[+] Please ensure you are connected to WiFi manually via GUI")
	if not connector.check_internet_connection():
		print("\n[-] No internet connection. Please connect to WiFi and try again.")
		sys.exit(1)
	
	# Test EC2 connection
	print("\n[STEP 2] Test EC2 Connection")
	print("-" * 40)
	if not connector.test_ec2_connection():
		print("\n[-] EC2 connection failed. Exiting.")
		sys.exit(1)
	
	# Start command processor (listens for commands from WebApp)
	print("\n[STEP 3] Start Command Processor")
	print("-" * 40)
	print("[+] SmartGate device is now ready for remote control")
	print("[+] Access the control panel at: http://{}:{}/test".format(EC2_IP, EC2_PORT))
	print("[+] Press Ctrl+C to stop the command processor")
	
	try:
		connector.process_commands()
	except KeyboardInterrupt:
		print("\n[+] Command processor stopped by user")
		connector.cleanup()
		sys.exit(0)

if __name__ == "__main__":
	main()