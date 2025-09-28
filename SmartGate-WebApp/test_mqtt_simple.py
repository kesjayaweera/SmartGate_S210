#!/usr/bin/env python3
"""
Simple MQTT test to verify endpoints
"""

import requests
import json
import time

def test_webapp_endpoints():
    """Test webapp MQTT endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing WebApp MQTT endpoints...")
    print("=" * 40)
    
    # Test 1: Check webapp is running
    try:
        response = requests.get(f"{base_url}/web-connect", timeout=5)
        print(f"✅ WebApp running: {response.status_code}")
    except Exception as e:
        print(f"❌ WebApp not running: {e}")
        print("   Make sure to start the webapp first:")
        print("   cd SmartGate-WebApp && python3 app.py")
        return False
    
    # Test 2: Test start_camera endpoint
    print("\nTesting /mqtt/start_camera...")
    try:
        response = requests.post(
            f"{base_url}/mqtt/start_camera",
            json={"device_id": "smartgate_device_001"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data.get('message', 'No message')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 3: Test get_latest_detection endpoint
    print("\nTesting /mqtt/get_latest_detection...")
    try:
        response = requests.get(f"{base_url}/mqtt/get_latest_detection", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data.get('message', 'No message')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    # Test 4: Test devices endpoint
    print("\nTesting /mqtt/devices...")
    try:
        response = requests.get(f"{base_url}/mqtt/devices", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data.get('count', 0)} devices")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
    
    return True

if __name__ == "__main__":
    test_webapp_endpoints()

