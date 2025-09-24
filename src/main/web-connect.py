#!/usr/bin/env python3
"""
SmartGate MQTT Client (Main Repository Version)
- Connects to EC2 MQTT broker
- Listens for gate control commands
- Executes commands using door_control.py functions
"""

import paho.mqtt.client as mqtt
import time
import json
import sys
from door_control import DoorControl
import Jetson.GPIO as GPIO

class SmartGateMQTTClient:
	"""MQTT client for SmartGate device"""
	
	def __init__(self, broker_ip, broker_port=1883):
		self.broker_ip = broker_ip
		self.broker_port = broker_port
		self.client = None
		self.is_connected = False
		
		# Initialize door controller
		self.door_controller = DoorControl()
		self.door_controller.init_door()
		
		# MQTT topics
		self.command_topic = "smartgate/commands"
		self.status_topic = "smartgate/status"
		self.device_id = "smartgate_device_001"
		
		print("[+] SmartGate MQTT Client initialized")
		print("[+] Broker: {}:{}".format(broker_ip, broker_port))
		print("[+] Device ID: {}".format(self.device_id))
		print("[+] Door controller initialized")
	
	def on_connect(self, client, userdata, flags, rc):
		"""Callback when connected to MQTT broker"""
		if rc == 0:
			print("[+] Connected to MQTT broker successfully")
			self.is_connected = True
			
			# Subscribe to command topic
			client.subscribe(self.command_topic)
			print("[+] Subscribed to topic: {}".format(self.command_topic))
			
			# Publish device status
			self.publish_status("online", "Device connected and ready")
			
		else:
			print("[-] Failed to connect to MQTT broker. Return code: {}".format(rc))
			self.is_connected = False
	
	def on_disconnect(self, client, userdata, rc):
		"""Callback when disconnected from MQTT broker"""
		print("[-] Disconnected from MQTT broker")
		self.is_connected = False
	
	def on_message(self, client, userdata, msg):
		"""Callback when message received"""
		try:
			topic = msg.topic
			payload = msg.payload.decode('utf-8')
			
			print("[+] Received message on topic: {}".format(topic))
			print("[+] Message payload: {}".format(payload))
			
			# Parse JSON command
			command_data = json.loads(payload)
			command = command_data.get('command')
			device_id = command_data.get('device_id', '')
			
			# Check if command is for this device
			if device_id and device_id != self.device_id:
				print("[+] Command not for this device ({}), ignoring".format(device_id))
				return
			
			print("[+] Executing command: {}".format(command))
			
			# Execute command using door_control.py functions
			if command == 'OPEN_DOOR':
				print("[+] Opening gate...")
				self.door_controller.open_door()
				self.publish_status("gate_opening", "Gate opening command executed")
				
			elif command == 'CLOSE_DOOR':
				print("[+] Closing gate...")
				self.door_controller.close_door()
				self.publish_status("gate_closing", "Gate closing command executed")
				
			elif command == 'STOP_DOOR':
				print("[+] Stopping gate...")
				self.door_controller.stop_door()
				self.publish_status("gate_stopped", "Gate stop command executed")
				
			elif command == 'STATUS':
				print("[+] Status requested")
				status = self.door_controller.get_door_status()
				print("[+] Door status: {}".format(status))
				self.publish_status("status_requested", "Status check completed: {}".format(status))
				
			else:
				print("[-] Unknown command: {}".format(command))
				self.publish_status("error", "Unknown command: {}".format(command))
				
		except json.JSONDecodeError:
			print("[-] Invalid JSON in message: {}".format(payload))
		except Exception as e:
			print("[-] Error processing message: {}".format(str(e)))
			self.publish_status("error", "Error processing command: {}".format(str(e)))
	
	def publish_status(self, status, message):
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
			print("[+] Published status: {} - {}".format(status, message))
		except Exception as e:
			print("[-] Failed to publish status: {}".format(str(e)))
	
	def connect(self):
		"""Connect to MQTT broker"""
		try:
			print("[+] Connecting to MQTT broker at {}:{}".format(self.broker_ip, self.broker_port))
			
			self.client = mqtt.Client(self.device_id)
			self.client.on_connect = self.on_connect
			self.client.on_disconnect = self.on_disconnect
			self.client.on_message = self.on_message
			
			# Connect to broker
			self.client.connect(self.broker_ip, self.broker_port, 60)
			
			# Start network loop
			self.client.loop_start()
			
			# Wait for connection
			timeout = 10
			start_time = time.time()
			while not self.is_connected and (time.time() - start_time) < timeout:
				time.sleep(0.1)
			
			if self.is_connected:
				print("[+] MQTT connection established successfully")
				return True
			else:
				print("[-] MQTT connection timeout")
				return False
				
		except Exception as e:
			print("[-] Failed to connect to MQTT broker: {}".format(str(e)))
			return False
	
	def disconnect(self):
		"""Disconnect from MQTT broker"""
		if self.client:
			self.client.loop_stop()
			self.client.disconnect()
			print("[+] Disconnected from MQTT broker")
	
	def run(self):
		"""Main run loop"""
		try:
			print("[+] SmartGate MQTT client running...")
			print("[+] Listening for commands on topic: {}".format(self.command_topic))
			print("[+] Press Ctrl+C to stop")
			
			# Keep running
			while True:
				time.sleep(1)
				
				# Publish periodic heartbeat
				if self.is_connected:
					self.publish_status("heartbeat", "Device online and listening")
					time.sleep(30)  # Heartbeat every 30 seconds
				else:
					print("[-] Not connected to MQTT broker, attempting reconnection...")
					self.connect()
					time.sleep(5)
					
		except KeyboardInterrupt:
			print("\n[+] Stopping SmartGate MQTT client...")
			self.publish_status("offline", "Device shutting down")
			self.disconnect()
			print("[+] SmartGate MQTT client stopped")

def main():
	"""Main function"""
	print("=" * 60)
	print("SmartGate MQTT Client (Main Repository)")
	print("=" * 60)
	
	# Configuration
	EC2_IP = "3.27.77.237"  # EC2 MQTT broker IP
	MQTT_PORT = 1883
	
	print("[+] EC2 MQTT Broker: {}:{}".format(EC2_IP, MQTT_PORT))
	print("[+] Commands will be executed using door_control.py functions")
	print("[+] Press Ctrl+C to stop")
	print("=" * 60)
	
	# Initialize MQTT client
	mqtt_client = SmartGateMQTTClient(EC2_IP, MQTT_PORT)
	
	# Connect to broker
	if not mqtt_client.connect():
		print("[-] Failed to connect to MQTT broker. Exiting.")
		sys.exit(1)
	
	# Run the client
	try:
		mqtt_client.run()
	except Exception as e:
		print("[-] Error running MQTT client: {}".format(str(e)))
	finally:
		mqtt_client.disconnect()

if __name__ == "__main__":
	main()