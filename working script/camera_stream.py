import cv2
import threading
import time
from typing import Optional, Callable

class CameraStream:
    """
    Independent camera stream handler that manages camera operations
    and provides frames to other components.
    """
    
    def __init__(self, frame_callback: Optional[Callable] = None):
        self.cap = None
        self.is_running = False
        self.frame_callback = frame_callback
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.stream_thread = None
        
    def gstreamer_pipeline(
        self,
        capture_width=1280,
        capture_height=720,
        display_width=1280,
        display_height=720,
        framerate=5,
        flip_method=0
    ):
        """Generate GStreamer pipeline for camera capture."""
        return (
            f"nvarguscamerasrc ! "
            f"video/x-raw(memory:NVMM), "
            f"width=(int){capture_width}, height=(int){capture_height}, "
            f"format=(string)NV12, framerate=(fraction){framerate}/1 ! "
            f"nvvidconv flip-method={flip_method} ! "
            f"video/x-raw, width=(int){display_width}, height=(int){display_height}, format=(string)BGRx ! "
            f"videoconvert ! "
            f"video/x-raw, format=(string)BGR ! appsink"
        )
    
    def start_stream(self):
        """Start the camera stream in a separate thread."""
        if self.is_running:
            print("Camera stream is already running.")
            return
            
        try:
            # Try GStreamer first
            print("[+] Trying GStreamer camera...")
            self.cap = cv2.VideoCapture(self.gstreamer_pipeline(), cv2.CAP_GSTREAMER)
            
            if not self.cap.isOpened():
                print("[-] GStreamer failed, trying OpenCV direct...")
                self.cap = cv2.VideoCapture(0)
                
                if not self.cap.isOpened():
                    print("[-] OpenCV direct failed, trying V4L2...")
                    self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            
            if not self.cap.isOpened():
                raise Exception("Failed to open camera with any method")
                
            self.is_running = True
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()
            print("Camera stream started successfully.")
            
        except Exception as e:
            print(f"Error starting camera stream: {e}")
            self.is_running = False
    
    def stop_stream(self):
        """Stop the camera stream and release resources."""
        self.is_running = False
        
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2.0)
            
        if self.cap:
            self.cap.release()
            self.cap = None
            
        print("Camera stream stopped.")
    
    def _stream_loop(self):
        """Main streaming loop running in separate thread."""
        while self.is_running:
            if self.cap and self.cap.isOpened():
                ret_val, frame = self.cap.read()
                if ret_val:
                    with self.frame_lock:
                        self.latest_frame = frame.copy()
                    
                    # Call the frame callback if provided
                    if self.frame_callback:
                        try:
                            self.frame_callback(frame.copy())
                        except Exception as e:
                            print(f"Error in frame callback: {e}")
                else:
                    print("Failed to read frame from camera")
                    time.sleep(0.1)
            else:
                print("Camera not available")
                time.sleep(1.0)
    
    def get_latest_frame(self) -> Optional[object]:
        """Get the latest captured frame."""
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None
    
    def capture_frame(self) -> Optional[object]:
        """Capture a single frame from the camera."""
        if self.cap and self.cap.isOpened():
            ret_val, frame = self.cap.read()
            if ret_val:
                return frame
        return None
    
    def is_available(self) -> bool:
        """Check if camera is available and running."""
        return self.is_running and self.cap is not None and self.cap.isOpened()


# ============================================================================
# HTTP CAMERA STREAMING SERVER
# ============================================================================
# This section provides HTTP server functionality for streaming camera feed
# via MJPEG format. Designed to work with reverse SSH tunnel for remote access.
# ============================================================================

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in separate threads"""
    daemon_threads = True
    allow_reuse_address = True


class CameraStreamHandler(BaseHTTPRequestHandler):
    """HTTP handler for camera streaming"""
    
    camera_stream = None
    detection_engine = None
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/stream':
            self.handle_camera_stream()
        elif self.path == '/health':
            self.handle_health_check()
        elif self.path == '/detection_image':
            self.handle_detection_image()
        else:
            self.send_error(404, "Not Found")
    
    def handle_camera_stream(self):
        """Stream camera feed as MJPEG"""
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'close')
            self.end_headers()
            
            print("[+] Client connected to camera stream")
            frame_count = 0
            last_time = time.time()
            
            while True:
                # Get latest frame from camera
                frame = self.camera_stream.get_latest_frame()
                
                if frame is not None:
                    # Process frame through AI detection if available
                    if self.detection_engine:
                        try:
                            detections = self.detection_engine.process_frame(frame)
                            if detections:
                                # Draw detection boxes on frame
                                for detection in detections:
                                    box = detection['box']
                                    cv2.rectangle(frame, (int(box[0]), int(box[1])), 
                                                (int(box[2]), int(box[3])), (0, 255, 0), 2)
                                    cv2.putText(frame, f"{detection['class']}: {detection['conf']:.2f}",
                                              (int(box[0]), int(box[1]) - 10),
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        except Exception as e:
                            print(f"[-] Error in AI detection: {e}")
                    
                    # Resize for streaming (good balance of quality/speed)
                    frame_resized = cv2.resize(frame, (640, 480))
                    
                    # Encode as JPEG
                    _, buffer = cv2.imencode('.jpg', frame_resized, [
                        cv2.IMWRITE_JPEG_QUALITY, 80
                    ])
                    
                    frame_bytes = buffer.tobytes()
                    
                    # Send frame
                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(frame_bytes)))
                    self.end_headers()
                    self.wfile.write(frame_bytes)
                    self.wfile.write(b'\r\n')
                    
                    frame_count += 1
                    
                    # Log FPS every 10 seconds
                    current_time = time.time()
                    if current_time - last_time >= 10.0:
                        fps = frame_count / (current_time - last_time)
                        print(f"[+] Camera stream: {fps:.1f} FPS to client")
                        frame_count = 0
                        last_time = current_time
                else:
                    # No frame available, wait a bit
                    time.sleep(0.1)
                
                # Control frame rate (target 15 FPS)
                time.sleep(0.067)
                
        except (ConnectionResetError, BrokenPipeError):
            print("[+] Client disconnected from camera stream")
        except Exception as e:
            print(f"[-] Error in camera stream: {e}")
    
    def handle_health_check(self):
        """Handle health check requests"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        health_data = {
            "status": "ok",
            "camera": "running" if self.camera_stream.is_available() else "not_available",
            "timestamp": time.time()
        }
        
        import json
        self.wfile.write(json.dumps(health_data).encode())
    
    def handle_detection_image(self):
        """
        Serve the latest detection image as a still image
        Processes camera frame through AI detection and returns JPEG with bounding boxes
        """
        print("[DEBUG] Detection image request received")
        
        try:
            # Get latest frame from camera with error checking
            if not self.camera_stream:
                print("[ERROR] Camera stream not available")
                self.send_error(503, "Camera stream not available")
                return
                
            frame = self.camera_stream.get_latest_frame()
            
            if frame is not None:
                print("[DEBUG] Frame retrieved, processing through AI detection...")
                
                # Process frame through AI detection if available
                if self.detection_engine:
                    try:
                        detections = self.detection_engine.process_frame(frame)
                        if detections and len(detections) > 0:
                            print("[INFO] Drawing {} detection boxes on frame".format(len(detections)))
                            # Draw detection boxes on frame
                            for i, detection in enumerate(detections):
                                try:
                                    box = detection.get('box', [0, 0, 0, 0])
                                    class_name = detection.get('class', 'Unknown')
                                    confidence = detection.get('conf', 0.0)
                                    
                                    # Draw bounding box
                                    cv2.rectangle(frame, (int(box[0]), int(box[1])), 
                                                (int(box[2]), int(box[3])), (0, 255, 0), 2)
                                    
                                    # Draw label
                                    label = "{}: {:.2f}".format(class_name, confidence)
                                    cv2.putText(frame, label,
                                              (int(box[0]), int(box[1]) - 10),
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                                    
                                    print("[DEBUG] Drew detection {}: {} at ({}, {})".format(
                                        i+1, label, int(box[0]), int(box[1])))
                                        
                                except Exception as box_e:
                                    print("[ERROR] Error drawing detection box {}: {}".format(i+1, box_e))
                        else:
                            print("[DEBUG] No detections found in frame")
                    except Exception as e:
                        print("[ERROR] Error in AI detection for image: {}".format(e))
                else:
                    print("[DEBUG] No detection engine available")
                
                # Resize for display
                try:
                    frame_resized = cv2.resize(frame, (640, 480))
                    print("[DEBUG] Frame resized to 640x480")
                except Exception as resize_e:
                    print("[ERROR] Error resizing frame: {}".format(resize_e))
                    self.send_error(500, "Error processing frame")
                    return
                
                # Encode as JPEG
                try:
                    _, buffer = cv2.imencode('.jpg', frame_resized, [
                        cv2.IMWRITE_JPEG_QUALITY, 90
                    ])
                    
                    if buffer is None:
                        print("[ERROR] Failed to encode frame as JPEG")
                        self.send_error(500, "Error encoding frame")
                        return
                        
                    frame_bytes = buffer.tobytes()
                    print("[DEBUG] Frame encoded as JPEG ({} bytes)".format(len(frame_bytes)))
                    
                except Exception as encode_e:
                    print("[ERROR] Error encoding frame as JPEG: {}".format(encode_e))
                    self.send_error(500, "Error encoding frame")
                    return
                
                # Send image
                try:
                    self.send_response(200)
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(frame_bytes)))
                    self.send_header('Cache-Control', 'no-cache')
                    self.end_headers()
                    self.wfile.write(frame_bytes)
                    print("[SUCCESS] Detection image sent successfully")
                    
                except Exception as send_e:
                    print("[ERROR] Error sending detection image: {}".format(send_e))
                
            else:
                # No frame available
                print("[WARNING] No camera frame available")
                self.send_error(404, "No camera frame available")
                
        except Exception as e:
            print("[ERROR] Unexpected error serving detection image: {}".format(e))
            self.send_error(500, "Error serving detection image")
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass


class HTTPCameraServer:
    """HTTP server for camera streaming with AI detection integration"""
    
    def __init__(self, camera_stream, detection_engine=None, port=8080):
        self.camera_stream = camera_stream
        self.detection_engine = detection_engine
        self.port = port
        self.server = None
        self.server_thread = None
        self.is_running = False
        
        print(f"[+] HTTP Camera Server initialized on port {port}")
        if detection_engine:
            print("[+] AI Detection Engine integrated")
    
    def start(self):
        """Start the HTTP server"""
        if self.is_running:
            print("[+] HTTP server already running")
            return True
        
        try:
            # Set class variables for handler
            CameraStreamHandler.camera_stream = self.camera_stream
            CameraStreamHandler.detection_engine = self.detection_engine
            
            # Create handler
            handler = CameraStreamHandler
            
            # Start server
            self.server = ThreadedHTTPServer(("0.0.0.0", self.port), handler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            
            self.is_running = True
            print(f"[+] HTTP camera server started on port {self.port}")
            print(f"[+] Stream URL: http://localhost:{self.port}/stream")
            print(f"[+] Health check: http://localhost:{self.port}/health")
            
            return True
            
        except Exception as e:
            print(f"[-] Failed to start HTTP server: {e}")
            return False
    
    def stop(self):
        """Stop the HTTP server"""
        if not self.is_running:
            print("[+] HTTP server not running")
            return
        
        try:
            print("[+] Stopping HTTP camera server...")
            self.is_running = False
            
            if self.server:
                self.server.shutdown()
                self.server.server_close()
            
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=3.0)
            
            print("[+] HTTP camera server stopped")
            
        except Exception as e:
            print(f"[-] Error stopping HTTP server: {e}")
    
    def is_available(self):
        """Check if server is running and accessible"""
        if not self.is_running:
            return False
        
        try:
            import socket
            # Test local connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', self.port))
            sock.close()
            return result == 0
        except:
            return False