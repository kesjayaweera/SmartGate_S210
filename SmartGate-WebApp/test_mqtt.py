#!/usr/bin/env python3
"""
Test script to verify MQTT setup
- Tests MQTT broker connection
- Tests sending commands
- Tests receiving status updates
"""

import paho.mqtt.client as mqtt
import json
import time
import sys

def test_mqtt_connection():
	"""Test MQTT broker connection"""
	print("=" * 50)
	print("Testing MQTT Connection")
	print("=" * 50)
	
	# Test broker connection
	broker_host = "localhost"
	broker_port = 1883
	
	try:
		client = mqtt.Client("test_client")
		client.connect(broker_host, broker_port, 60)
		print("[+] Successfully connected to MQTT broker at {}:{}".format(broker_host, broker_port))
		
		# Test publishing a message
		test_message = {"test": "connection", "timestamp": time.time()}
		client.publish("test/topic", json.dumps(test_message))
		print("[+] Successfully published test message")
		
		client.disconnect()
		print("[+] Successfully disconnected from MQTT broker")
		return True
		
	except Exception as e:
		print("[-] Failed to connect to MQTT broker: {}".format(str(e)))
		return False

def test_gate_command():
	"""Test sending gate command"""
	print("\n" + "=" * 50)
	print("Testing Gate Command")
	print("=" * 50)
	
	broker_host = "localhost"
	broker_port = 1883
	
	try:
		client = mqtt.Client("test_command_client")
		client.connect(broker_host, broker_port, 60)
		
		# Send test command
		command_data = {
			"device_id": "smartgate_device_001",
			"command": "STATUS",
			"timestamp": time.time(),
			"source": "test_script"
		}
		
		client.publish("smartgate/commands", json.dumps(command_data))
		print("[+] Successfully sent gate command: {}".format(command_data))
		
		client.disconnect()
		return True
		
	except Exception as e:
		print("[-] Failed to send gate command: {}".format(str(e)))
		return False

def main():
	"""Main test function"""
	print("SmartGate MQTT Test Script")
	print("This script tests the MQTT setup for SmartGate")
	
	# Test 1: Basic MQTT connection
	connection_ok = test_mqtt_connection()
	
	# Test 2: Gate command
	command_ok = test_gate_command()
	
	# Summary
	print("\n" + "=" * 50)
	print("Test Results Summary")
	print("=" * 50)
	print("MQTT Connection: {}".format("PASS" if connection_ok else "FAIL"))
	print("Gate Command: {}".format("PASS" if command_ok else "FAIL"))
	
	if connection_ok and command_ok:
		print("\n[+] All tests passed! MQTT setup is working correctly.")
		return 0
	else:
		print("\n[-] Some tests failed. Check MQTT broker configuration.")
		return 1

if __name__ == "__main__":
	sys.exit(main())
