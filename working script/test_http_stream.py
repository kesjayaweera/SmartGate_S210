#!/usr/bin/env python3
"""
Test script for HTTP stream + reverse tunnel implementation
"""

import time
import requests
import subprocess
import sys
import signal
import threading

def test_http_camera_server():
    """Test the HTTP camera server locally"""
    print("=" * 50)
    print("Testing HTTP Camera Server")
    print("=" * 50)
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8080/health", timeout=5)
        if response.status_code == 200:
            print("[PASS] HTTP camera server health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f" HTTP camera server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" HTTP camera server not accessible: {e}")
        return False
    
    return True

def test_reverse_tunnel():
    """Test reverse tunnel connectivity"""
    print("\n" + "=" * 50)
    print("Testing Reverse Tunnel")
    print("=" * 50)
    
    try:
        # Test if tunnel port is accessible
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("[PASS] Reverse tunnel health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"Reverse tunnel health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Reverse tunnel not accessible: {e}")
        print("   Make sure the reverse tunnel is running")
        return False
    
    return True

def test_webapp_endpoints():
    """Test webapp endpoints"""
    print("\n" + "=" * 50)
    print("Testing WebApp Endpoints")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Camera control is now handled via HTTP + reverse tunnel
    # No MQTT camera endpoints needed
    print("[INFO] Camera control now uses HTTP + reverse tunnel (no MQTT endpoints)")
    
    # Test stream redirect
    try:
        response = requests.get(f"{base_url}/stream", timeout=5, allow_redirects=False)
        if response.status_code == 302:
            print(" Stream redirect working")
            print(f"   Redirects to: {response.headers.get('Location', 'No location')}")
        else:
            print(f" Stream redirect failed: {response.status_code}")
            return False
    except Exception as e:
        print(f" Stream redirect error: {e}")
        return False
    
    return True

def test_full_integration():
    """Test full integration"""
    print("\n" + "=" * 50)
    print("Full Integration Test")
    print("=" * 50)
    
    print("1. Starting web-connect.py...")
    print("   (This will start camera, HTTP server, reverse tunnel, and AI detection)")
    print("   Run this in a separate terminal:")
    print("   cd 'working script' && python3 web-connect.py")
    print()
    
    print("2. Starting webapp...")
    print("   Run this in another terminal:")
    print("   cd SmartGate-WebApp && python3 app.py")
    print()
    
    print("3. Test the camera stream:")
    print("   Open browser to: http://localhost:8000/test.html")
    print("   Click 'Start Camera Stream'")
    print()
    
    print("4. Expected behavior:")
    print("   - Camera stream should start via HTTP + reverse tunnel")
    print("   - AI detection should be running in background")
    print("   - Stream should be accessible at: http://localhost:8001/stream")
    print("   - Webapp should redirect /stream to tunneled stream")
    print()

def main():
    """Main test function"""
    print("SmartGate HTTP Stream + Reverse Tunnel Test")
    print("=" * 60)
    
    # Test individual components
    http_ok = test_http_camera_server()
    tunnel_ok = test_reverse_tunnel()
    webapp_ok = test_webapp_endpoints()
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    print(f"HTTP Camera Server: {'PASS' if http_ok else 'FAIL'}")
    print(f"Reverse Tunnel:     {'PASS' if tunnel_ok else ' FAIL'}")
    print(f"WebApp Endpoints:   {'PASS' if webapp_ok else 'FAIL'}")
    
    if http_ok and tunnel_ok and webapp_ok:
        print("\n -------- All tests passed! System is ready.")
        test_full_integration()
    else:
        print("\nSome tests failed. Check the components above.")
        print("\nTroubleshooting:")
        if not http_ok:
            print("- Make sure camera_stream.py is working")
            print("- Check if port 8080 is available")
        if not tunnel_ok:
            print("- Make sure reverse tunnel is running")
            print("- Check SSH connection to EC2")
            print("- Verify port 8001 is available")
        if not webapp_ok:
            print("- Make sure webapp is running on port 8000")
            print("- Check MQTT broker is running")

if __name__ == "__main__":
    main()
