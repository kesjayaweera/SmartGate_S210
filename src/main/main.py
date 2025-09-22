import signal
import sys
import threading
import time
from typing import Optional

import Jetson.GPIO as GPIO
from door_control import DoorControl
import io_control as io

from http_server import Initialize_Server, Shutdown_Server, set_latest_frame, set_door_controller_reference, Fetch_Queued_Command
from camera_stream import CameraStream
from detection_engine import DetectionEngine
from gate_states import State
from json_config import JsonConfig

class SmartGateController:
    """
    Main controller that coordinates the web server, camera stream, and detection engine.
    Handles door control and state management.
    """
    
    def __init__(self):
        self.web_server = None
        self.camera_stream = None
        self.detection_engine = None
        self.door_controller = None
        self.config = None
        self.is_running = False
        self.main_thread = None
        
    def initialize(self):
        """Initialize all components of the SmartGate system."""
        try:
            print("Initializing SmartGate system...")
            
            # Initialize configuration
            self.config = JsonConfig()
            server_config = self.config.get_server_config()
            
            # Initialize GPIO
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(7, GPIO.OUT, initial=GPIO.LOW)
            
            # Initialize IO pins and door control
            io.set_all_pins()
            self.door_controller = DoorControl()
            
            # Initialize camera stream
            self.camera_stream = CameraStream(frame_callback=self._on_frame_received)
            
            # Initialize detection engine
            self.detection_engine = DetectionEngine(detection_callback=self._on_detection_complete)
            
            # Initialize and start web server
            self.web_server = Initialize_Server(server_config)
            set_door_controller_reference(self.door_controller)
            
            print("SmartGate system initialized successfully.")
            
        except Exception as e:
            print(f"Error initializing SmartGate system: {e}")
            self.cleanup()
            raise
    
    def start(self):
        """Start all components of the SmartGate system."""
        if self.is_running:
            print("SmartGate system is already running.")
            return
            
        try:
            print("Starting SmartGate system...")
            
            # Start camera stream
            self.camera_stream.start_stream()
            
            # Start detection engine
            self.detection_engine.start_detection()
            
            # Start main control loop
            self.is_running = True
            self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
            self.main_thread.start()
            
            print("SmartGate system started successfully.")
            
        except Exception as e:
            print(f"Error starting SmartGate system: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop all components of the SmartGate system."""
        print("Stopping SmartGate system...")
        
        self.is_running = False
        
        # Stop detection engine
        if self.detection_engine:
            self.detection_engine.stop_detection()
        
        # Stop camera stream
        if self.camera_stream:
            self.camera_stream.stop_stream()
        
        # Wait for main thread to finish
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=3.0)
        
        print("SmartGate system stopped.")
    
    def cleanup(self):
        """Clean up all resources."""
        print("Cleaning up SmartGate system...")
        
        self.stop()
        
        # Clean up GPIO
        io.all_pins_off()
        GPIO.cleanup()
        
        # Shutdown web server
        if self.web_server:
            Shutdown_Server(self.web_server)
        
        print("SmartGate system cleaned up.")
    
    def _main_loop(self):
        """Main control loop that handles door control and command processing."""
        while self.is_running:
            try:
                # Check for commands from HTTP server
                self._process_commands()
                
                # Handle door control based on current state
                self._handle_door_control()
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(1.0)
    
    def _process_commands(self):
        """Process commands from HTTP server."""
        command = Fetch_Queued_Command()
        if command:
            if command == 'OPEN_DOOR':
                print("Received OPEN_DOOR command")
                self.detection_engine.set_state(State.DOOR_OPEN)
            elif command == 'CLOSE_DOOR':
                print("Received CLOSE_DOOR command")
                self.detection_engine.set_state(State.DOOR_CLOSE)
    
    def _handle_door_control(self):
        """Handle door control based on current state."""
        current_state = self.detection_engine.get_state()
        
        if current_state == State.DOOR_OPEN:
            self._handle_door_open()
        elif current_state == State.DOOR_CLOSE:
            self._handle_door_close()
        elif current_state == State.IDLE:
            self._handle_idle_door_control()
    
    def _handle_door_open(self):
        """Handle door opening."""
        print("Opening door.")
        
        if not self.door_controller.is_door_fully_open():
            self.door_controller.open_door()
        else:
            print('Door stopped on opening')
            self.door_controller.stop_door()
        
        self.detection_engine.set_state(State.IDLE)
    
    def _handle_door_close(self):
        """Handle door closing."""
        print("Closing door.")
        
        if not self.door_controller.is_door_fully_closed():
            self.door_controller.close_door()
        else:
            print('Door stopped on closing')
            self.door_controller.stop_door()
        
        self.detection_engine.set_state(State.IDLE)
    
    def _handle_idle_door_control(self):
        """Handle door control during idle state."""
        # Ensure the motor stops when Hall Effect sensors are detected during IDLE state
        if self.door_controller.is_door_fully_closed() and self.door_controller.is_door_closing:
            self.door_controller.stop_door()
            print("Door fully closed, stopping motor.")
        elif self.door_controller.is_door_fully_open() and self.door_controller.is_door_opening:
            self.door_controller.stop_door()
            print("Door fully open, stopping motor.")
    
    def _on_frame_received(self, frame):
        """Callback for when a new frame is received from camera."""
        # Update the latest frame for HTTP server streaming
        set_latest_frame(frame.copy())
        
        # If we're in DETECT state, process the frame
        if self.detection_engine.get_state() == State.DETECT:
            self.detection_engine.process_frame(frame)
    
    def _on_detection_complete(self, detections, frame):
        """Callback for when detection is complete."""
        # Update the latest frame with detection results
        set_latest_frame(frame.copy())
        print(f"Detection complete: {len(detections)} objects detected")

def signal_handler(sig, frame):
    """Handle keyboard interrupt signal."""
    print('[+] Ctrl+C Detected... Exiting...')
    if 'controller' in globals():
        controller.cleanup()
    sys.exit(0)

def main():
    """Main entry point for the SmartGate application."""
    global controller
    
    # Set up signal handler for keyboard interrupt
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Create and initialize controller
        controller = SmartGateController()
        controller.initialize()
        
        # Start the system
        controller.start()
        
        # Keep the main thread alive
        print("SmartGate system is running. Press Ctrl+C to exit.")
        while controller.is_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Received keyboard interrupt")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        if 'controller' in globals():
            controller.cleanup()

if __name__ == "__main__":
    main()

