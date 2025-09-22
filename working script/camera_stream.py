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
            self.cap = cv2.VideoCapture(self.gstreamer_pipeline(), cv2.CAP_GSTREAMER)
            if not self.cap.isOpened():
                raise Exception("Failed to open camera")
                
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
