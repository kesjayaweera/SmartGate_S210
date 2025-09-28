#!/usr/bin/env python3
"""
SmartGate MQTT Client
- Connects to EC2 MQTT broker
- Listens for gate control commands
- Executes commands using test.py functions
"""

import paho.mqtt.client as mqtt
import time
import json
import sys
import subprocess
import threading
import socket
from test import open_gate, close_gate, print_status
import io_control as io
import Jetson.GPIO as GPIO

class SmartGateMQTTClient:
	"""MQTT client for SmartGate device"""
	
	def __init__(self, broker_ip, broker_port=1883):
		self.broker_ip = broker_ip
		self.broker_port = broker_port
		self.client = None
		self.is_connected = False
		
		# MQTT topics
		self.command_topic = "smartgate/commands"
		self.status_topic = "smartgate/status"
		self.device_id = "smartgate_device_001"
		
		# Camera streaming settings
		self.camera_stream_active = False
		self.camera_stream_thread = None
		self.camera_stream_interval = 0.05  # Send frame every 50ms for 20 FPS
		self.frame_quality = 60  # Lower quality for faster transmission
		
		print("[+] SmartGate MQTT Client initialized")
		print("[+] Broker: {}:{}".format(broker_ip, broker_port))
		print("[+] Device ID: {}".format(self.device_id))
		print("[+] 3.56PM")
	
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
			
			# Execute command using test.py functions
			if command == 'OPEN_DOOR':
				print("[+] Opening gate...")
				open_gate()
				self.publish_status("gate_opening", "Gate opening command executed")
				
			elif command == 'CLOSE_DOOR':
				print("[+] Closing gate...")
				close_gate()
				self.publish_status("gate_closing", "Gate closing command executed")
				
			elif command == 'STOP_DOOR':
				print("[+] Stopping gate...")
				io.set_val('IN3', False)
				io.set_val('IN4', False)
				io.all_pins_off()
				self.publish_status("gate_stopped", "Gate stop command executed")
				
			elif command == 'STATUS':
				print("[+] Status requested")
				print_status()
				self.publish_status("status_requested", "Status check completed")
				
			elif command == 'START_CAMERA':
				print("[+] Camera start requested")
				if self.start_camera_stream():
					self.publish_status("camera_started", "Camera stream started via MQTT")
				else:
					self.publish_status("camera_error", "Failed to start camera stream")
					
			elif command == 'STOP_CAMERA':
				print("[+] Camera stop requested")
				self.stop_camera_stream()
				self.publish_status("camera_stopped", "Camera stream stopped")
				
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
	
	def get_local_ip(self):
		"""Get local IP address"""
		try:
			# Connect to a remote address to determine local IP
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.connect(("8.8.8.8", 80))
			local_ip = s.getsockname()[0]
			s.close()
			return local_ip
		except Exception as e:
			print("[-] Error getting local IP: {}".format(e))
			return "unknown"
	
	def start_camera_stream(self):
		"""Start camera streaming using the working camera_stream.py method"""
		if self.camera_stream_active:
			print("[+] Camera stream already active")
			return True
			
		try:
			# Use the working camera_stream.py method
			from camera_stream import CameraStream
			
			print("[+] Initializing camera using working camera_stream.py method...")
			self.camera_stream = CameraStream()
			self.camera_stream.start_stream()
			
			# Wait for camera to initialize
			time.sleep(3)
			
			if self.camera_stream.is_available():
				print("[+] Camera stream initialized successfully")
				
				# Start MQTT streaming
				self.camera_stream_active = True
				self.camera_stream_thread = threading.Thread(target=self._camera_stream_loop, daemon=True)
				self.camera_stream_thread.start()
				
				print("[+] Camera streaming started via MQTT")
				return True
			else:
				print("[-] Camera not available after initialization")
				return False
				
		except Exception as e:
			print("[-] Error starting camera stream: {}".format(e))
			return False
	
	def _try_camera_stream_class(self):
		"""Try to initialize CameraStream class with proper GStreamer pipeline"""
		try:
			from camera_stream import CameraStream
			camera = CameraStream()
			camera.start_stream()
			time.sleep(3)  # Wait longer for GStreamer initialization
			
			# Test if camera is actually working
			if camera.is_available():
				# Try to get a frame to verify it's working
				frame = camera.get_latest_frame()
				if frame is not None and frame.size > 0:
					print("[+] CameraStream with GStreamer pipeline working!")
					return camera
				else:
					print("[-] CameraStream initialized but no frames available")
					camera.stop_stream()
					return None
			else:
				print("[-] CameraStream not available after initialization")
				return None
		except Exception as e:
			print(f"[-] CameraStream class failed: {e}")
			return None
	
	def _create_mock_camera(self):
		"""Create a mock camera for testing MQTT streaming"""
		import cv2
		import numpy as np
		
		class MockCamera:
			def __init__(self):
				self.frame_count = 0
				print("[+] Mock camera created for testing")
			
			def read(self):
				# Create a test pattern frame
				self.frame_count += 1
				frame = np.zeros((480, 640, 3), dtype=np.uint8)
				
				# Add some visual content
				cv2.putText(frame, f"Mock Camera Frame {self.frame_count}", (50, 50), 
						   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
				cv2.putText(frame, f"Time: {time.time():.1f}", (50, 100), 
						   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
				
				# Add a moving circle
				center_x = int(320 + 200 * np.sin(self.frame_count * 0.1))
				center_y = int(240 + 100 * np.cos(self.frame_count * 0.1))
				cv2.circle(frame, (center_x, center_y), 30, (0, 0, 255), -1)
				
				return True, frame
			
			def isOpened(self):
				return True
			
			def release(self):
				print("[+] Mock camera released")
		
		return MockCamera()
	
	def _kill_existing_camera_processes(self):
		"""Kill any existing camera processes that might be blocking access"""
		try:
			import subprocess
			import time
			
			# Kill any existing nvargus processes
			try:
				subprocess.run(['sudo', 'pkill', '-f', 'nvargus'], check=False)
				print("[+] Killed existing nvargus processes")
			except:
				pass
			
			# Kill any existing GStreamer processes
			try:
				subprocess.run(['sudo', 'pkill', '-f', 'gst-launch'], check=False)
				print("[+] Killed existing GStreamer processes")
			except:
				pass
			
			# Kill any existing camera-related processes
			try:
				subprocess.run(['sudo', 'pkill', '-f', 'camera'], check=False)
				print("[+] Killed existing camera processes")
			except:
				pass
			
			# Wait a moment for processes to fully terminate
			time.sleep(2)
			
			# Restart nvargus daemon
			try:
				subprocess.run(['sudo', 'systemctl', 'restart', 'nvargus-daemon'], check=False)
				print("[+] Restarted nvargus daemon")
				time.sleep(1)
			except:
				pass
				
		except Exception as e:
			print(f"[-] Error killing camera processes: {e}")
	
	def _try_direct_gstreamer(self):
		"""Try direct GStreamer pipeline for Jetson camera"""
		try:
			import cv2
			
			# Use the same GStreamer pipeline as the working camera_stream.py
			gstreamer_pipeline = (
				"nvarguscamerasrc ! "
				"video/x-raw(memory:NVMM), "
				"width=(int)1280, height=(int)720, "
				"format=(string)NV12, framerate=(fraction)30/1 ! "
				"nvvidconv flip-method=0 ! "
				"video/x-raw, width=(int)1280, height=(int)720, format=(string)BGRx ! "
				"videoconvert ! "
				"video/x-raw, format=(string)BGR ! appsink"
			)
			
			camera = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)
			if camera.isOpened():
				print("[+] Direct GStreamer pipeline successful!")
				return camera
			else:
				print("[-] Direct GStreamer pipeline failed to open")
				camera.release()
				return None
		except Exception as e:
			print(f"[-] Direct GStreamer pipeline failed: {e}")
			return None
	
	def stop_camera_stream(self):
		"""Stop camera streaming"""
		if not self.camera_stream_active:
			print("[+] No active camera stream to stop")
			return
			
		try:
			print("[+] Stopping camera stream...")
			self.camera_stream_active = False
			
			# Wait for stream thread to finish
			if self.camera_stream_thread and self.camera_stream_thread.is_alive():
				print("[+] Waiting for camera stream thread to finish...")
				self.camera_stream_thread.join(timeout=3.0)
				if self.camera_stream_thread.is_alive():
					print("[-] Camera stream thread did not stop gracefully")
			
			# Stop camera stream
			if hasattr(self, 'camera_stream') and self.camera_stream:
				if hasattr(self.camera_stream, 'stop_stream'):
					print("[+] Stopping CameraStream...")
					self.camera_stream.stop_stream()
				elif hasattr(self.camera_stream, 'release'):
					print("[+] Releasing OpenCV VideoCapture...")
					self.camera_stream.release()
				else:
					print("[+] Camera stream object cleaned up")
			
			# Clear references
			self.camera_stream = None
			self.camera_stream_thread = None
			
			print("[+] Camera stream stopped successfully")
			
		except Exception as e:
			print("[-] Error stopping camera stream: {}".format(e))
	
	def _camera_stream_loop(self):
		"""Simple camera streaming loop using working camera_stream.py method"""
		import cv2
		import base64
		
		frame_count = 0
		last_time = time.time()
		
		print("[+] Starting camera streaming loop...")
		
		while self.camera_stream_active and self.is_connected:
			try:
				# Get latest frame from camera_stream.py
				frame = self.camera_stream.get_latest_frame()
				
				if frame is not None and frame.size > 0:
					# Resize frame for faster transmission
					frame_resized = cv2.resize(frame, (480, 360))
					
					# Encode frame as JPEG (good quality)
					_, buffer = cv2.imencode('.jpg', frame_resized, [
						cv2.IMWRITE_JPEG_QUALITY, 80
					])
					
					# Convert to base64 for MQTT transmission
					frame_b64 = base64.b64encode(buffer).decode('utf-8')
					
					# Create camera message
					camera_data = {
						"device_id": self.device_id,
						"frame": frame_b64,
						"timestamp": time.time(),
						"width": 480,
						"height": 360,
						"frame_id": frame_count
					}
					
					# Send via MQTT
					self.client.publish("smartgate/camera", json.dumps(camera_data))
					
					frame_count += 1
					
					# Log FPS every 5 seconds
					current_time = time.time()
					if current_time - last_time >= 5.0:
						fps = frame_count / (current_time - last_time)
						print(f"[+] Camera streaming at {fps:.1f} FPS")
						frame_count = 0
						last_time = current_time
				
				time.sleep(0.1)  # 10 FPS - good balance
				
			except Exception as e:
				print("[-] Error in camera stream loop: {}".format(e))
				time.sleep(1.0)
		
		print("[+] Camera streaming loop ended")
	
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
	print("SmartGate MQTT Client")
	print("=" * 60)
	
	# Configuration
	EC2_IP = "3.27.77.237"  # EC2 MQTT broker IP
	MQTT_PORT = 1883
	
	print("[+] EC2 MQTT Broker: {}:{}".format(EC2_IP, MQTT_PORT))
	print("[+] Commands will be executed using test.py functions")
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