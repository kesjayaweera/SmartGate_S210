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
    
    MODIFIED: Added dashboard notification functionality via MQTT
    """
    
    def __init__(self, detection_callback: Optional[Callable] = None, mqtt_client=None, device_id="smartgate_device_001"):
        self.config = JsonConfig()
        self.model = None
        self.decider = None
        self.detection_callback = detection_callback
        self.is_running = False
        self.detection_thread = None
        self.current_state = State.IDLE
        self.object_list = []
        self.state_lock = threading.Lock()
        
        # MODIFIED: Added MQTT client and dashboard notification settings
        self.mqtt_client = mqtt_client
        self.device_id = device_id
        self.last_detection_time = 0
        self.detection_cooldown = 2.0  # Send at most one detection every 2 seconds
        
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
        
        MODIFIED: Added automatic dashboard notification via MQTT
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
            
            # MODIFIED: Send detection to dashboard via MQTT if detections found
            if detections and self.mqtt_client:
                import time
                current_time = time.time()
                if current_time - self.last_detection_time >= self.detection_cooldown:
                    self._send_detection_to_dashboard(detections)
                    self.last_detection_time = current_time
            
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
    
    # MODIFIED: Added dashboard notification method
    def _send_detection_to_dashboard(self, detections):
        """
        Send detection notification to dashboard via MQTT
        
        MODIFIED: This method was added to send detections to dashboard
        Processes detection data and publishes to MQTT with comprehensive error handling
        """
        print("[DEBUG] Attempting to send detection to dashboard")
        
        if not detections or not self.mqtt_client:
            print("[WARNING] Cannot send detection - no detections or MQTT client")
            return
        
        try:
            import json
            import time
            
            print("[DEBUG] Processing {} detections for dashboard".format(len(detections)))
            
            # Get the most confident detection with error checking
            try:
                best_detection = max(detections, key=lambda x: x.get('conf', 0))
                print("[DEBUG] Best detection: {} (confidence: {:.2f})".format(
                    best_detection.get('class', 'Unknown'), 
                    best_detection.get('conf', 0.0)))
            except Exception as e:
                print("[ERROR] Error finding best detection: {}".format(e))
                return
            
            # Prepare detection data with error checking
            try:
                detection_data = {
                    "device_id": self.device_id,
                    "animal": best_detection.get('class', 'Unknown'),
                    "confidence": float(best_detection.get('conf', 0.0)),
                    "timestamp": time.time(),
                    "all_detections": [
                        {
                            "class": det.get('class', 'Unknown'),
                            "confidence": float(det.get('conf', 0.0))
                        }
                        for det in detections
                    ]
                }
                print("[DEBUG] Detection data prepared: {}".format(detection_data['animal']))
            except Exception as e:
                print("[ERROR] Error preparing detection data: {}".format(e))
                return
            
            # Publish to MQTT with multiple fallback methods
            try:
                json_data = json.dumps(detection_data)
                print("[DEBUG] JSON data prepared ({} bytes)".format(len(json_data)))
                
                # Try different MQTT client methods
                published = False
                
                if hasattr(self.mqtt_client, 'publish'):
                    try:
                        result = self.mqtt_client.publish("smartgate/detections", json_data)
                        print("[SUCCESS] Detection sent via mqtt_client.publish (result: {})".format(result))
                        published = True
                    except Exception as e:
                        print("[ERROR] Failed mqtt_client.publish: {}".format(e))
                
                if not published and hasattr(self.mqtt_client, 'client') and hasattr(self.mqtt_client.client, 'publish'):
                    try:
                        result = self.mqtt_client.client.publish("smartgate/detections", json_data)
                        print("[SUCCESS] Detection sent via mqtt_client.client.publish (result: {})".format(result.rc))
                        published = True
                    except Exception as e:
                        print("[ERROR] Failed mqtt_client.client.publish: {}".format(e))
                
                if not published:
                    print("[ERROR] No valid MQTT publish method found")
                    
            except Exception as e:
                print("[ERROR] Error publishing detection to MQTT: {}".format(e))
            
        except Exception as e:
            print("[ERROR] Unexpected error sending detection to dashboard: {}".format(e))
            print("[ERROR] Detection data: {}".format(detections))


# ============================================================================
# MODIFICATION NOTES
# ============================================================================
# The DetectionEngine class has been modified to include dashboard notification
# functionality. The following changes were made:
#
# 1. Added mqtt_client and device_id parameters to __init__()
# 2. Added dashboard notification settings (last_detection_time, detection_cooldown)
# 3. Modified process_frame() to automatically send detections to dashboard
# 4. Added _send_detection_to_dashboard() method
#
# The old separate DetectionEngineWithDashboard class has been removed as
# the functionality is now integrated into the main DetectionEngine class.
# ============================================================================
