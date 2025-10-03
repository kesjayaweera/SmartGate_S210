#!/usr/bin/env python3
"""
MQTT Client for SmartGate WebApp
- Connects to MQTT broker
- Sends commands to SmartGate devices
- Receives status updates from devices
"""

import paho.mqtt.client as mqtt
import json
import time
import os
from datetime import datetime

class SmartGateMQTTClient:
	"""MQTT client for webapp to control SmartGate devices"""
	
	def __init__(self):
		self.broker_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
		self.broker_port = int(os.getenv('MQTT_BROKER_PORT', 1883))
		self.client = None
		self.is_connected = False
		
		# MQTT topics
		self.command_topic = "smartgate/commands"
		self.status_topic = "smartgate/status"
		self.detection_topic = "smartgate/detections"
		
		# Device tracking
		self.connected_devices = {}
		self.device_status = {}
		self.latest_detection = None
		
		print("[+] SmartGate WebApp MQTT Client initialized")
		print("[+] Broker: {}:{}".format(self.broker_host, self.broker_port))
	
	def on_connect(self, client, userdata, flags, rc):
		"""Callback when connected to MQTT broker"""
		if rc == 0:
			print("[+] WebApp connected to MQTT broker successfully")
			self.is_connected = True
			
			# Subscribe to status topic to receive device updates
			client.subscribe(self.status_topic)
			print("[+] Subscribed to status topic: {}".format(self.status_topic))
			
			# Subscribe to detection topic to receive animal detections
			client.subscribe(self.detection_topic)
			print("[+] Subscribed to detection topic: {}".format(self.detection_topic))
			
		else:
			print("[-] WebApp failed to connect to MQTT broker. Return code: {}".format(rc))
			self.is_connected = False
	
	def on_disconnect(self, client, userdata, rc):
		"""Callback when disconnected from MQTT broker"""
		print("[-] WebApp disconnected from MQTT broker")
		self.is_connected = False
	
	def on_message(self, client, userdata, msg):
		"""Callback when message received"""
		try:
			topic = msg.topic
			payload = msg.payload.decode('utf-8')
			
			print("[+] WebApp received message on topic: {}".format(topic))
			print("[+] Message payload: {}".format(payload))
			
			# Parse JSON message
			message_data = json.loads(payload)
			device_id = message_data.get('device_id')
			
			# Handle detection messages
			if topic == self.detection_topic:
				animal = message_data.get('animal')
				confidence = message_data.get('confidence')
				timestamp = message_data.get('timestamp')
				all_detections = message_data.get('all_detections', [])
				
				if animal:
					self.latest_detection = {
						"animal": animal,
						"confidence": confidence,
						"timestamp": timestamp,
						"device_id": device_id,
						"all_detections": all_detections
					}
					print("[+] Latest detection updated: {} ({}%)".format(animal, confidence * 100))
				return
			
			# Handle status messages
			status = message_data.get('status')
			message = message_data.get('message')
			timestamp = message_data.get('timestamp')
			
			if device_id:
				# Update device tracking
				self.connected_devices[device_id] = {
					"last_seen": datetime.now().isoformat(),
					"status": status,
					"message": message,
					"timestamp": timestamp
				}
				
				self.device_status[device_id] = status
				
				print("[+] Device {} status updated: {} - {}".format(device_id, status, message))
				
		except json.JSONDecodeError:
			print("[-] Invalid JSON in status message: {}".format(payload))
		except Exception as e:
			print("[-] Error processing status message: {}".format(str(e)))
	
	def connect(self):
		"""Connect to MQTT broker"""
		try:
			print("[+] WebApp connecting to MQTT broker at {}:{}".format(self.broker_host, self.broker_port))
			
			self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "smartgate_webapp")
			self.client.on_connect = self.on_connect
			self.client.on_disconnect = self.on_disconnect
			self.client.on_message = self.on_message
			
			# Connect to broker
			self.client.connect(self.broker_host, self.broker_port, 60)
			
			# Start network loop
			self.client.loop_start()
			
			# Wait for connection
			timeout = 10
			start_time = time.time()
			while not self.is_connected and (time.time() - start_time) < timeout:
				time.sleep(0.1)
			
			if self.is_connected:
				print("[+] WebApp MQTT connection established successfully")
				return True
			else:
				print("[-] WebApp MQTT connection timeout")
				return False
				
		except Exception as e:
			print("[-] WebApp failed to connect to MQTT broker: {}".format(str(e)))
			return False
	
	def send_command(self, device_id, command):
		"""Send command to specific SmartGate device"""
		if not self.is_connected:
			print("[-] Not connected to MQTT broker")
			return False
		
		command_data = {
			"device_id": device_id,
			"command": command,
			"timestamp": time.time(),
			"source": "webapp"
		}
		
		try:
			self.client.publish(self.command_topic, json.dumps(command_data))
			print("[+] WebApp sent command to device {}: {}".format(device_id, command))
			return True
		except Exception as e:
			print("[-] Failed to send command: {}".format(str(e)))
			return False
	
	def get_connected_devices(self):
		"""Get list of connected devices"""
		return self.connected_devices
	
	def get_device_status(self, device_id):
		"""Get status of a specific device"""
		if device_id in self.connected_devices:
			device_info = self.connected_devices[device_id]
			return {
				"status": device_info.get("status", "unknown"),
				"message": device_info.get("message", ""),
				"last_seen": device_info.get("last_seen"),
				"timestamp": device_info.get("timestamp"),
				"is_online": True
			}
		return {
			"status": "offline",
			"message": "Device not connected",
			"last_seen": None,
			"timestamp": None,
			"is_online": False
		}
	
	def get_all_devices(self):
		"""Get all connected devices"""
		return self.connected_devices
	
	def is_device_online(self, device_id):
		"""Check if device is online"""
		return device_id in self.connected_devices
	
	def get_latest_detection(self):
		"""Get latest animal detection data"""
		return self.latest_detection
	
	def disconnect(self):
		"""Disconnect from MQTT broker"""
		if self.client:
			self.client.loop_stop()
			self.client.disconnect()
			print("[+] WebApp disconnected from MQTT broker")

# Global MQTT client instance
mqtt_client = None

def get_mqtt_client():
	"""Get or create global MQTT client instance"""
	global mqtt_client
	if mqtt_client is None:
		mqtt_client = SmartGateMQTTClient()
		mqtt_client.connect()
	return mqtt_client

def send_gate_command(device_id, command):
	"""Send command to gate device"""
	client = get_mqtt_client()
	return client.send_command(device_id, command)

def get_connected_gates():
	"""Get list of connected gate devices"""
	client = get_mqtt_client()
	return client.get_connected_devices()