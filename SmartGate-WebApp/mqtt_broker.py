#!/usr/bin/env python3
"""
MQTT Broker Management for SmartGate WebApp
- Starts and manages MQTT broker
- Provides broker status information
"""

import subprocess
import time
import os
import signal
import sys

class MQTTBrokerManager:
	"""Manages MQTT broker process"""
	
	def __init__(self):
		self.broker_process = None
		self.broker_host = "localhost"
		self.broker_port = 1883
		self.is_running = False
		
		print("[+] MQTT Broker Manager initialized")
	
	def start_broker(self):
		"""Start MQTT broker process"""
		try:
			if self.is_running:
				print("[+] MQTT broker already running")
				return True
			
			print("[+] Starting MQTT broker...")
			
			# Start mosquitto broker
			cmd = ["mosquitto", "-c", "/mosquitto/config/mosquitto.conf"]
			self.broker_process = subprocess.Popen(
				cmd,
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				preexec_fn=os.setsid
			)
			
			# Wait a moment for broker to start
			time.sleep(2)
			
			# Check if process is still running
			if self.broker_process.poll() is None:
				self.is_running = True
				print("[+] MQTT broker started successfully on {}:{}".format(self.broker_host, self.broker_port))
				return True
			else:
				print("[-] Failed to start MQTT broker")
				return False
				
		except Exception as e:
			print("[-] Error starting MQTT broker: {}".format(str(e)))
			return False
	
	def stop_broker(self):
		"""Stop MQTT broker process"""
		try:
			if not self.is_running or not self.broker_process:
				print("[+] MQTT broker not running")
				return True
			
			print("[+] Stopping MQTT broker...")
			
			# Send SIGTERM to process group
			os.killpg(os.getpgid(self.broker_process.pid), signal.SIGTERM)
			
			# Wait for process to terminate
			self.broker_process.wait(timeout=10)
			
			self.is_running = False
			print("[+] MQTT broker stopped successfully")
			return True
			
		except subprocess.TimeoutExpired:
			print("[-] MQTT broker did not stop gracefully, forcing termination...")
			os.killpg(os.getpgid(self.broker_process.pid), signal.SIGKILL)
			self.is_running = False
			return True
		except Exception as e:
			print("[-] Error stopping MQTT broker: {}".format(str(e)))
			return False
	
	def get_status(self):
		"""Get broker status"""
		return {
			"is_running": self.is_running,
			"host": self.broker_host,
			"port": self.broker_port,
			"pid": self.broker_process.pid if self.broker_process else None
		}

# Global broker manager instance
broker_manager = MQTTBrokerManager()

def start_mqtt_broker():
	"""Start MQTT broker"""
	return broker_manager.start_broker()

def stop_mqtt_broker():
	"""Stop MQTT broker"""
	return broker_manager.stop_broker()

def get_broker_status():
	"""Get MQTT broker status"""
	return broker_manager.get_status()

# Cleanup on exit
import atexit
atexit.register(stop_mqtt_broker)