import cv2
import imutils
import threading
import time
from typing import List, Dict, Optional, Callable
from YoloDetTRT import YoloTRT
import io_control as io
from ruleset_decider import RulesetDecider
from gate_states import State
from json_config import JsonConfig

class DetectionEngine:
    """
    Handles motion detection, YOLO inference, and decision making.
    Operates independently from the web server and camera stream.
    """
    
    def __init__(self, detection_callback: Optional[Callable] = None):
        self.config = JsonConfig()
        self.model = None
        self.decider = None
        self.detection_callback = detection_callback
        self.is_running = False
        self.detection_thread = None
        self.current_state = State.IDLE
        self.object_list = []
        self.state_lock = threading.Lock()
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize YOLO model and ruleset decider."""
        try:
            # Get configurations
            model_config = self.config.get_model_config()
            rules_config = self.config.get_rules_config()
            
            # Initialize YOLOv5 model via TensorRT engine
            self.model = YoloTRT(model_config)
            
            # Initialize ruleset decider
            self.decider = RulesetDecider(rules_config)
            
            print("Detection engine components initialized successfully.")
            
        except Exception as e:
            print(f"Error initializing detection engine: {e}")
            raise
    
    def start_detection(self):
        """Start the detection engine in a separate thread."""
        if self.is_running:
            print("Detection engine is already running.")
            return
            
        self.is_running = True
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        print("Detection engine started successfully.")
    
    def stop_detection(self):
        """Stop the detection engine."""
        self.is_running = False
        
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=2.0)
            
        print("Detection engine stopped.")
    
    def _detection_loop(self):
        """Main detection loop running in separate thread."""
        while self.is_running:
            try:
                with self.state_lock:
                    current_state = self.current_state
                
                if current_state == State.IDLE:
                    self._handle_idle_state()
                elif current_state == State.DETECT:
                    self._handle_detect_state()
                elif current_state == State.DECISION:
                    self._handle_decision_state()
                elif current_state == State.DELAY:
                    self._handle_delay_state()
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                print(f"Error in detection loop: {e}")
                time.sleep(1.0)
    
    def _handle_idle_state(self):
        """Handle IDLE state - check for motion detection."""
        # Check for PIR sensor activation
        if io.get_val('PIR'):
            print("Motion detected, transitioning to DETECT state.")
            with self.state_lock:
                self.current_state = State.DETECT
        else:
            with self.state_lock:
                self.current_state = State.IDLE
    
    def _handle_detect_state(self):
        """Handle DETECT state - perform object detection."""
        print("Detecting objects.")
        
        # This will be called by the main controller with a frame
        # For now, we'll wait for the frame to be provided
        with self.state_lock:
            self.current_state = State.DECISION
    
    def _handle_decision_state(self):
        """Handle DECISION state - make decisions based on detected objects."""
        print("Making decision based on detected objects.")
        
        if self.decider and self.object_list:
            with self.state_lock:
                self.current_state = self.decider.decide(self.object_list)
        else:
            with self.state_lock:
                self.current_state = State.IDLE
    
    def _handle_delay_state(self):
        """Handle DELAY state - wait for delay period."""
        print("Delaying operation.")
        # Implementation for delay logic would go here
        with self.state_lock:
            self.current_state = State.IDLE
    
    def process_frame(self, frame) -> List[Dict]:
        """
        Process a frame for object detection.
        Returns list of detected objects.
        """
        if not self.model or frame is None:
            return []
        
        try:
            # Resize the frame for YOLOv5
            img = imutils.resize(frame, width=600)
            
            # Perform inference
            detections, t = self.model.Inference(img)
            
            # Extract object classes
            self.object_list = [obj['class'] for obj in detections]
            
            # Call detection callback if provided
            if self.detection_callback:
                try:
                    self.detection_callback(detections, img)
                except Exception as e:
                    print(f"Error in detection callback: {e}")
            
            return detections
            
        except Exception as e:
            print(f"Error processing frame: {e}")
            return []
    
    def set_state(self, new_state: State):
        """Set the current state of the detection engine."""
        with self.state_lock:
            self.current_state = new_state
    
    def get_state(self) -> State:
        """Get the current state of the detection engine."""
        with self.state_lock:
            return self.current_state
    
    def get_detected_objects(self) -> List[str]:
        """Get the list of detected object classes."""
        return self.object_list.copy()
    
    def is_motion_detected(self) -> bool:
        """Check if motion is currently detected by PIR sensor."""
        return io.get_val('PIR')
    
    def cleanup(self):
        """Clean up detection engine resources."""
        self.stop_detection()
        print("Detection engine cleaned up.")

