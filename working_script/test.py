#!/usr/bin/env python3
"""
SmartGate Control Script with Hall Effect Sensors
This script opens or closes the gate until Hall Effect sensors detect completion.
"""

import sys
import time
import signal
import io_control as io
import Jetson.GPIO as GPIO

def signal_handler(sig, frame):
    """Handle Ctrl+C for clean shutdown."""
    print("\n[*] Stopping gate...")
    io.set_val('IN3', False)
    io.set_val('IN4', False)
    io.all_pins_off()
    GPIO.cleanup()
    print("[+] Gate stopped and cleaned up!")
    sys.exit(0)

def is_gate_fully_open():
    """
    Check if gate is fully open using Hall Effect sensors.
    When fully open: OPEN sensor = 0 (LOW), CLOSE sensor = 1 (HIGH)
    """
    open_sensor = io.get_val('OPEN')
    close_sensor = io.get_val('CLOSE')
    return open_sensor == 0 and close_sensor == 1

def is_gate_fully_closed():
    """
    Check if gate is fully closed using Hall Effect sensors.
    When fully closed: OPEN sensor = 1 (HIGH), CLOSE sensor = 0 (LOW)
    """
    open_sensor = io.get_val('OPEN')
    close_sensor = io.get_val('CLOSE')
    return open_sensor == 1 and close_sensor == 0

def open_gate():
    """
    Open the gate until Hall Effect sensor detects it's fully open.
    """
    print("[*] Starting gate OPEN sequence...")
    print("[*] Press Ctrl+C to stop at any time")
    
    # Initialize GPIO pins
    io.set_all_pins()
    
    # Check initial sensor states
    open_sensor = io.get_val('OPEN')
    close_sensor = io.get_val('CLOSE')
    print(f"[*] Initial sensor states - OPEN: {open_sensor}, CLOSE: {close_sensor}")
    
    # Check if already fully open
    if is_gate_fully_open():
        print("[!] Gate is already fully open!")
        GPIO.cleanup()
        return
    
    # Enable motor
    io.set_val('ENB', True)
    
    # Set motor direction to open
    io.set_val('IN3', False)
    io.set_val('IN4', True)
    
    print("[+] Gate opening...")
    print("[*] Waiting for Hall Effect sensor to detect fully open position...")
    
    start_time = time.time()
    check_count = 0
    
    # Keep opening until Hall Effect sensor triggers
    while not is_gate_fully_open():
        time.sleep(0.1)  # Check sensor every 100ms
        check_count += 1
        
        # Print status every 2 seconds
        if check_count % 20 == 0:
            elapsed = time.time() - start_time
            open_sensor = io.get_val('OPEN')
            close_sensor = io.get_val('CLOSE')
            print(f"[*] Still opening... ({elapsed:.1f}s elapsed)")
            print(f"    Sensor states - OPEN: {open_sensor}, CLOSE: {close_sensor}")
        
        # Safety timeout after 60 seconds
        if time.time() - start_time > 30:
            print("[!] Timeout after 60 seconds - stopping gate")
            print("[!] Hall Effect sensor may not be working properly")
            break
    
    # Stop the motor
    print("[*] Stopping motor...")
    io.set_val('IN3', False)
    io.set_val('IN4', False)
    
    # Final sensor check
    if is_gate_fully_open():
        elapsed = time.time() - start_time
        print(f"[+] Gate fully opened! (took {elapsed:.1f} seconds)")
    else:
        print("[!] Gate stopped but may not be fully open")
        open_sensor = io.get_val('OPEN')
        close_sensor = io.get_val('CLOSE')
        print(f"    Final sensor states - OPEN: {open_sensor}, CLOSE: {close_sensor}")
    
    # Clean up
    io.all_pins_off()
    GPIO.cleanup()
    print("[+] Done!")

def close_gate():
    """
    Close the gate until Hall Effect sensor detects it's fully closed.
    """
    print("[*] Starting gate CLOSE sequence...")
    print("[*] Press Ctrl+C to stop at any time")
    
    # Initialize GPIO pins
    io.set_all_pins()
    
    # Check initial sensor states
    open_sensor = io.get_val('OPEN')
    close_sensor = io.get_val('CLOSE')
    print(f"[*] Initial sensor states - OPEN: {open_sensor}, CLOSE: {close_sensor}")
    
    # Check if already fully closed
    if is_gate_fully_closed():
        print("[!] Gate is already fully closed!")
        GPIO.cleanup()
        return
    
    # Enable motor
    io.set_val('ENB', True)
    
    # Set motor direction to close
    io.set_val('IN3', True)
    io.set_val('IN4', False)
    
    print("[+] Gate closing...")
    print("[*] Waiting for Hall Effect sensor to detect fully closed position...")
    
    start_time = time.time()
    check_count = 0
    
    # Keep closing until Hall Effect sensor triggers
    while not is_gate_fully_closed():
        time.sleep(0.1)  # Check sensor every 100ms
        check_count += 1
        
        # Print status every 2 seconds
        if check_count % 20 == 0:
            elapsed = time.time() - start_time
            open_sensor = io.get_val('OPEN')
            close_sensor = io.get_val('CLOSE')
            print(f"[*] Still closing... ({elapsed:.1f}s elapsed)")
            print(f"    Sensor states - OPEN: {open_sensor}, CLOSE: {close_sensor}")
        
        # Safety timeout after 60 seconds
        if time.time() - start_time > 30:
            print("[!] Timeout after 60 seconds - stopping gate")
            print("[!] Hall Effect sensor may not be working properly")
            break
    
    # Stop the motor
    print("[*] Stopping motor...")
    io.set_val('IN3', False)
    io.set_val('IN4', False)
    
    # Final sensor check
    if is_gate_fully_closed():
        elapsed = time.time() - start_time
        print(f"[+] Gate fully closed! (took {elapsed:.1f} seconds)")
    else:
        print("[!] Gate stopped but may not be fully closed")
        open_sensor = io.get_val('OPEN')
        close_sensor = io.get_val('CLOSE')
        print(f"    Final sensor states - OPEN: {open_sensor}, CLOSE: {close_sensor}")
    
    # Clean up
    io.all_pins_off()
    GPIO.cleanup()
    print("[+] Done!")

def print_status():
    """Print current gate status based on Hall Effect sensors."""
    io.set_all_pins()
    
    open_sensor = io.get_val('OPEN')
    close_sensor = io.get_val('CLOSE')
    
    print("="*50)
    print("Gate Status:")
    print(f"  Hall Effect Sensors - OPEN: {open_sensor}, CLOSE: {close_sensor}")
    
    if is_gate_fully_open():
        print("  Position: FULLY OPEN")
    elif is_gate_fully_closed():
        print("  Position: FULLY CLOSED")
    else:
        print("  Position: PARTIALLY OPEN")
    print("="*50)
    
    GPIO.cleanup()

def main():
    """Main function."""
    # Set up signal handler for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("="*50)
        print("SmartGate Control Script")
        print("="*50)
        print("Usage:")
        print("  python3 gate_control.py open    - Open the gate")
        print("  python3 gate_control.py close   - Close the gate")
        print("  python3 gate_control.py status  - Check gate status")
        print("="*50)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "open":
        open_gate()
    elif command == "close":
        close_gate()
    elif command == "status":
        print_status()
    else:
        print(f"[!] Unknown command: {command}")
        print("Use 'open', 'close', or 'status'")
        sys.exit(1)

if __name__ == "__main__":
    main()
