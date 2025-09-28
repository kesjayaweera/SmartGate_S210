#!/usr/bin/env python3
"""
Test script to verify MQTT endpoints are working
"""

import requests
import json

def test_mqtt_endpoints():
    """Test MQTT endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing MQTT endpoints...")
    
    # Test 1: Check if webapp is running
    try:
        response = requests.get(f"{base_url}/web-connect")
        print(f"✅ WebApp is running: {response.status_code}")
    except Exception as e:
        print(f"❌ WebApp not running: {e}")
        return
    
    # Test 2: Test start_camera endpoint
    try:
        response = requests.post(
            f"{base_url}/mqtt/start_camera",
            json={"device_id": "smartgate_device_001"},
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Start camera endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Start camera endpoint failed: {e}")
    
    # Test 3: Test get_latest_detection endpoint
    try:
        response = requests.get(f"{base_url}/mqtt/get_latest_detection")
        print(f"✅ Get latest detection endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Get latest detection endpoint failed: {e}")
    
    # Test 4: Test devices endpoint
    try:
        response = requests.get(f"{base_url}/mqtt/devices")
        print(f"✅ Get devices endpoint: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Get devices endpoint failed: {e}")

if __name__ == "__main__":
    test_mqtt_endpoints()

