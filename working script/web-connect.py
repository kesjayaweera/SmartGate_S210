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
		"""
		Initialize SmartGate MQTT Client
		Handles MQTT communication, camera streaming, and AI detection
		"""
		print("[DEBUG] Initializing SmartGate MQTT Client...")
		
		try:
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
			self.http_server = None
			self.reverse_tunnel = None
			self.use_http_stream = True  # Use HTTP stream
			
			# AI Detection Engine
			self.detection_engine = None
			self.detection_active = False
			
			print("[SUCCESS] SmartGate MQTT Client initialized successfully")
			print("[INFO] Broker: {}:{}".format(broker_ip, broker_port))
			print("[INFO] Device ID: {}".format(self.device_id))
			print("[INFO] Camera streaming method: HTTP + Reverse Tunnel")
			print("[INFO] AI Detection: Enabled with dashboard notifications")
			
		except Exception as e:
			print("[ERROR] Failed to initialize SmartGate MQTT Client: {}".format(e))
			raise
	
	def on_connect(self, client, userdata, flags, rc):
		"""
		Callback when connected to MQTT broker
		Handles successful connection and subscription setup
		"""
		print("[DEBUG] MQTT connection callback triggered with return code: {}".format(rc))
		
		if rc == 0:
			print("[SUCCESS] Connected to MQTT broker successfully")
			self.is_connected = True
			
			try:
				# Subscribe to command topic
				result = client.subscribe(self.command_topic)
				print("[INFO] Subscribed to command topic: {} (result: {})".format(self.command_topic, result))
				
				# Publish device status
				self.publish_status("online", "Device connected and ready")
				print("[INFO] Published initial online status")
				
			except Exception as e:
				print("[ERROR] Error during MQTT setup after connection: {}".format(e))
				self.is_connected = False
			
		else:
			print("[ERROR] Failed to connect to MQTT broker. Return code: {}".format(rc))
			print("[ERROR] Connection failed - check broker IP and port")
			self.is_connected = False
	
	def on_disconnect(self, client, userdata, rc):
		"""
		Callback when disconnected from MQTT broker
		Handles disconnection and cleanup
		"""
		print("[WARNING] Disconnected from MQTT broker (return code: {})".format(rc))
		self.is_connected = False
		
		if rc != 0:
			print("[ERROR] Unexpected disconnection - attempting reconnection...")
		else:
			print("[INFO] Normal disconnection")
	
	def on_message(self, client, userdata, msg):
		"""
		Callback when message received from MQTT broker
		Processes incoming commands and executes appropriate actions
		"""
		print("[DEBUG] MQTT message received")
		
		try:
			topic = msg.topic
			payload = msg.payload.decode('utf-8')
			
			print("[INFO] Received message on topic: {}".format(topic))
			print("[DEBUG] Message payload: {}".format(payload))
			
			# Parse JSON command
			try:
				command_data = json.loads(payload)
			except json.JSONDecodeError as e:
				print("[ERROR] Invalid JSON in MQTT message: {}".format(e))
				print("[ERROR] Raw payload: {}".format(payload))
				return
			
			command = command_data.get('command')
			device_id = command_data.get('device_id', '')
			
			print("[DEBUG] Parsed command: {}, device_id: {}".format(command, device_id))
			
			# Check if command is for this device
			if device_id and device_id != self.device_id:
				print("[INFO] Command not for this device ({}), ignoring".format(device_id))
				return
			
			print("[INFO] Executing command: {} for device: {}".format(command, self.device_id))
			
			# Execute command using test.py functions
			try:
				if command == 'OPEN_DOOR':
					print("[INFO] Opening gate...")
					try:
						open_gate()
						self.publish_status("gate_opening", "Gate opening command executed")
						print("[SUCCESS] Gate opening command executed successfully")
					except Exception as e:
						print("[ERROR] Failed to open gate: {}".format(e))
						self.publish_status("gate_error", "Failed to open gate: {}".format(e))
					
				elif command == 'CLOSE_DOOR':
					print("[INFO] Closing gate...")
					try:
						close_gate()
						self.publish_status("gate_closing", "Gate closing command executed")
						print("[SUCCESS] Gate closing command executed successfully")
					except Exception as e:
						print("[ERROR] Failed to close gate: {}".format(e))
						self.publish_status("gate_error", "Failed to close gate: {}".format(e))
					
				elif command == 'STOP_DOOR':
					print("[INFO] Stopping gate...")
					try:
						io.set_val('IN3', False)
						io.set_val('IN4', False)
						io.all_pins_off()
						self.publish_status("gate_stopped", "Gate stop command executed")
						print("[SUCCESS] Gate stop command executed successfully")
					except Exception as e:
						print("[ERROR] Failed to stop gate: {}".format(e))
						self.publish_status("gate_error", "Failed to stop gate: {}".format(e))
					
				elif command == 'STATUS':
					print("[INFO] Status requested")
					try:
						print_status()
						self.publish_status("status_requested", "Status check completed")
						print("[SUCCESS] Status check completed successfully")
					except Exception as e:
						print("[ERROR] Failed to get status: {}".format(e))
						self.publish_status("status_error", "Failed to get status: {}".format(e))
					
				elif command == 'START_CAMERA':
					print("[INFO] Camera start requested (legacy MQTT command - using HTTP stream)")
					try:
						if self.start_camera_stream():
							self.publish_status("camera_started", "Camera stream started via HTTP + reverse tunnel")
							print("[SUCCESS] Camera stream started successfully")
						else:
							self.publish_status("camera_error", "Failed to start camera stream")
							print("[ERROR] Failed to start camera stream")
					except Exception as e:
						print("[ERROR] Exception during camera start: {}".format(e))
						self.publish_status("camera_error", "Exception during camera start: {}".format(e))
					
				elif command == 'STOP_CAMERA':
					print("[INFO] Camera stop requested (legacy MQTT command - using HTTP stream)")
					try:
						self.stop_camera_stream()
						self.publish_status("camera_stopped", "Camera stream stopped")
						print("[SUCCESS] Camera stream stopped successfully")
					except Exception as e:
						print("[ERROR] Failed to stop camera stream: {}".format(e))
						self.publish_status("camera_error", "Failed to stop camera stream: {}".format(e))
					
				else:
					print("[WARNING] Unknown command received: {}".format(command))
					self.publish_status("error", "Unknown command: {}".format(command))
					
			except Exception as e:
				print("[ERROR] Exception during command execution: {}".format(e))
				self.publish_status("error", "Exception during command execution: {}".format(e))
				
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
		"""
		Start camera streaming using HTTP server + reverse tunnel + AI detection
		Initializes camera, detection engine, HTTP server, and reverse tunnel
		"""
		print("[DEBUG] Starting camera stream...")
		
		if self.camera_stream_active:
			print("[WARNING] Camera stream already active - skipping start")
			return True
			
		try:
			# Import required modules with error checking
			print("[DEBUG] Importing required modules...")
			try:
				from camera_stream import CameraStream, HTTPCameraServer
				from reverse_tunnel import ReverseTunnelManager
				from detection_engine import DetectionEngine
				print("[SUCCESS] All modules imported successfully")
			except ImportError as e:
				print("[ERROR] Failed to import required modules: {}".format(e))
				return False
			
			# Initialize camera stream
			print("[INFO] Initializing camera using HTTP stream method...")
			try:
				self.camera_stream = CameraStream()
				if not self.camera_stream:
					print("[ERROR] Failed to create CameraStream instance")
					return False
				
				print("[DEBUG] Starting camera stream...")
				self.camera_stream.start_stream()
				print("[INFO] Camera stream start command sent")
				
				# Wait for camera to initialize
				print("[DEBUG] Waiting for camera initialization...")
				time.sleep(3)
				
				if self.camera_stream.is_available():
					print("[SUCCESS] Camera stream initialized successfully")
				else:
					print("[ERROR] Camera not available after initialization")
					return False
					
			except Exception as e:
				print("[ERROR] Failed to initialize camera stream: {}".format(e))
				return False
			
			# Initialize AI Detection Engine
			print("[INFO] Initializing AI Detection Engine...")
			try:
				self.detection_engine = DetectionEngine(
					detection_callback=self._on_detection_result,
					mqtt_client=self,
					device_id=self.device_id
				)
				if not self.detection_engine:
					print("[ERROR] Failed to create DetectionEngine instance")
					return False
				
				print("[DEBUG] Starting AI detection...")
				self.detection_engine.start_detection()
				self.detection_active = True
				print("[SUCCESS] AI Detection Engine started with dashboard notifications")
				
			except Exception as e:
				print("[ERROR] Failed to initialize AI Detection Engine: {}".format(e))
				return False
			
			# Start HTTP server
			print("[INFO] Starting HTTP camera server...")
			try:
				self.http_server = HTTPCameraServer(self.camera_stream, self.detection_engine, port=8080)
				if not self.http_server:
					print("[ERROR] Failed to create HTTPCameraServer instance")
					return False
				
				if self.http_server.start():
					print("[SUCCESS] HTTP camera server started on port 8080")
				else:
					print("[ERROR] Failed to start HTTP server")
					return False
					
			except Exception as e:
				print("[ERROR] Failed to start HTTP server: {}".format(e))
				return False
			
			# Start reverse tunnel
			print("[INFO] Starting reverse tunnel to EC2...")
			try:
				self.reverse_tunnel = ReverseTunnelManager(
					ec2_ip=self.broker_ip,
					ec2_user="ubuntu",
					local_port=8080,
					remote_port=8001
				)
				if not self.reverse_tunnel:
					print("[ERROR] Failed to create ReverseTunnelManager instance")
					self.http_server.stop()
					return False
				
				if self.reverse_tunnel.start_tunnel():
					print("[SUCCESS] Reverse tunnel started (local:8080 -> remote:8001)")
					self.camera_stream_active = True
					print("[SUCCESS] Camera streaming started via HTTP + reverse tunnel + AI detection")
					return True
				else:
					print("[ERROR] Failed to start reverse tunnel")
					self.http_server.stop()
					return False
					
			except Exception as e:
				print("[ERROR] Failed to start reverse tunnel: {}".format(e))
				self.http_server.stop()
				return False
				
		except Exception as e:
			print("[ERROR] Unexpected error starting camera stream: {}".format(e))
			# Cleanup on failure
			try:
				if hasattr(self, 'http_server') and self.http_server:
					self.http_server.stop()
				if hasattr(self, 'detection_engine') and self.detection_engine:
					self.detection_engine.stop_detection()
			except Exception as cleanup_e:
				print("[ERROR] Error during cleanup: {}".format(cleanup_e))
			return False
	
	
	def _on_detection_result(self, detections, frame):
		"""
		Callback for AI detection results
		Processes detection results and publishes them via MQTT
		"""
		print("[DEBUG] Detection callback triggered")
		
		try:
			if detections and len(detections) > 0:
				print("[SUCCESS] AI Detection: {} objects detected".format(len(detections)))
				
				# Prepare detection info for MQTT
				detection_info = {
					"device_id": self.device_id,
					"detections": detections,
					"timestamp": time.time(),
					"frame_count": len(detections)
				}
				
				# Publish detection results via MQTT
				try:
					if self.client and self.is_connected:
						result = self.client.publish("smartgate/detections", json.dumps(detection_info))
						print("[SUCCESS] Detection data published to MQTT (result: {})".format(result.rc))
					else:
						print("[WARNING] MQTT client not connected - cannot publish detection")
				except Exception as mqtt_e:
					print("[ERROR] Failed to publish detection via MQTT: {}".format(mqtt_e))
				
				# Log detected objects
				for i, detection in enumerate(detections):
					class_name = detection.get('class', 'Unknown')
					confidence = detection.get('conf', 0.0)
					print("[INFO] Detection {}: {} (confidence: {:.2f}%)".format(i+1, class_name, confidence * 100))
			else:
				print("[DEBUG] No detections in callback")
				
		except Exception as e:
			print("[ERROR] Error in detection callback: {}".format(e))
			print("[ERROR] Detection data: {}".format(detections))
	
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
			print("[+] Stopping camera stream and AI detection...")
			self.camera_stream_active = False
			
			# Stop AI Detection Engine
			if self.detection_engine and self.detection_active:
				print("[+] Stopping AI Detection Engine...")
				self.detection_engine.stop_detection()
				self.detection_active = False
				print("[+] AI Detection Engine stopped")
			
			# Stop reverse tunnel
			if self.reverse_tunnel:
				print("[+] Stopping reverse tunnel...")
				self.reverse_tunnel.stop_tunnel()
				self.reverse_tunnel = None
			
			# Stop HTTP server
			if self.http_server:
				print("[+] Stopping HTTP camera server...")
				self.http_server.stop()
				self.http_server = None
			
			# Wait for stream thread to finish (if using MQTT fallback)
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
	"""
	Main function - Entry point for SmartGate MQTT Client
	Initializes and runs the MQTT client with comprehensive error handling
	"""
	print("=" * 60)
	print("SmartGate MQTT Client - Starting...")
	print("=" * 60)
	
	# Configuration
	EC2_IP = "3.27.77.237"  # EC2 MQTT broker IP
	MQTT_PORT = 1883
	
	print("[INFO] EC2 MQTT Broker: {}:{}".format(EC2_IP, MQTT_PORT))
	print("[INFO] Commands will be executed using test.py functions")
	print("[INFO] Camera streaming: HTTP + Reverse Tunnel + AI Detection")
	print("[INFO] Press Ctrl+C to stop")
	print("=" * 60)
	
	# Initialize MQTT client with error checking
	print("[DEBUG] Initializing MQTT client...")
	try:
		mqtt_client = SmartGateMQTTClient(EC2_IP, MQTT_PORT)
		print("[SUCCESS] MQTT client initialized")
	except Exception as e:
		print("[ERROR] Failed to initialize MQTT client: {}".format(e))
		sys.exit(1)
	
	# Connect to broker with error checking
	print("[DEBUG] Connecting to MQTT broker...")
	try:
		if not mqtt_client.connect():
			print("[ERROR] Failed to connect to MQTT broker. Exiting.")
			sys.exit(1)
		print("[SUCCESS] Connected to MQTT broker")
	except Exception as e:
		print("[ERROR] Exception during MQTT connection: {}".format(e))
		sys.exit(1)
	
	# Run the client with comprehensive error handling
	print("[INFO] Starting MQTT client main loop...")
	try:
		mqtt_client.run()
	except KeyboardInterrupt:
		print("[INFO] Received keyboard interrupt (Ctrl+C)")
		print("[INFO] Shutting down gracefully...")
	except Exception as e:
		print("[ERROR] Unexpected error running MQTT client: {}".format(e))
		print("[ERROR] Stack trace:", exc_info=True)
	finally:
		print("[DEBUG] Cleaning up MQTT client...")
		try:
			mqtt_client.disconnect()
			print("[SUCCESS] MQTT client disconnected")
		except Exception as e:
			print("[ERROR] Error during MQTT client cleanup: {}".format(e))
		print("[INFO] SmartGate MQTT Client stopped")

if __name__ == "__main__":
	main()