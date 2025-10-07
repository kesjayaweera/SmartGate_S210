#!/usr/bin/env python3
"""
Simple Multi-Camera System for SmartGate
Supports multiple ArduCam cameras with GStreamer pipelines
"""

import cv2
import threading
import time
import logging
import subprocess
import os
from typing import Optional, Callable, Dict, List
from enum import Enum

logger = logging.getLogger(__name__)

class CameraStatus(Enum):
    """Camera status states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

def detect_available_cameras(max_cameras: int = 4) -> List[int]:
    """
    Simple camera detection - check for video devices
    Returns list of available camera IDs (0, 1, 2, etc.)
    """
    available_cameras = []
    
    logger.info(f"Scanning for cameras (testing 0 to {max_cameras-1})...")
    
    # Check for physical video devices
    for i in range(max_cameras):
        if os.path.exists(f"/dev/video{i}"):
            available_cameras.append(i)
    
    logger.info(f"Found video devices: {available_cameras}")
    return available_cameras

class Camera:
    """
    Simple camera class for handling a single camera
    Supports ArduCam cameras connected via cam0, cam1 ports
    """
    
    def __init__(self, camera_id: int, frame_callback: Optional[Callable] = None):
        self.camera_id = camera_id
        self.frame_callback = frame_callback
        
        # Camera state
        self.cap = None
        self.is_running = False
        self.status = CameraStatus.DISCONNECTED
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.stream_thread = None
        
        # Statistics
        self.frame_count = 0
        self.error_count = 0
        self.start_time = None
        
        # Configuration - simple defaults
        self.capture_width = 640
        self.capture_height = 480
        self.framerate = 15
        
        logger.info(f"[CAMERA_{camera_id}] Initialized")
    
    def gstreamer_pipeline(self) -> str:
        """Generate GStreamer pipeline for ArduCam camera"""
        pipeline = (
            f"nvarguscamerasrc sensor-id={self.camera_id} ! "
            f"video/x-raw(memory:NVMM), "
            f"width=(int){self.capture_width}, height=(int){self.capture_height}, "
            f"format=(string)NV12, framerate=(fraction){self.framerate}/1 ! "
            f"nvvidconv ! "
            f"video/x-raw, width=(int){self.capture_width}, height=(int){self.capture_height}, format=(string)BGRx ! "
            f"videoconvert ! "
            f"video/x-raw, format=(string)BGR ! appsink"
        )
        return pipeline
    
    def start_camera(self) -> bool:
        """Start the camera stream - simple initialization"""
        if self.is_running:
            logger.warning(f"[CAMERA_{self.camera_id}] Already running")
            return True
        
        logger.info(f"[CAMERA_{self.camera_id}] Starting camera")
        self.status = CameraStatus.CONNECTING
        
        try:
            # Try V4L2 first (more reliable for IMX477)
            logger.info(f"[CAMERA_{self.camera_id}] Attempting V4L2 initialization...")
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_V4L2)
            
            if self.cap.isOpened():
                logger.info(f"[CAMERA_{self.camera_id}] V4L2 camera opened successfully")
                self.status = CameraStatus.CONNECTED
            else:
                logger.warning(f"[CAMERA_{self.camera_id}] V4L2 failed, trying GStreamer...")
                self.cap.release()
                
                # Try GStreamer pipeline as fallback
                pipeline = self.gstreamer_pipeline()
                self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
                
                if self.cap.isOpened():
                    logger.info(f"[CAMERA_{self.camera_id}] GStreamer camera opened successfully")
                    self.status = CameraStatus.CONNECTED
                else:
                    logger.error(f"[CAMERA_{self.camera_id}] Both V4L2 and GStreamer failed")
                    self.status = CameraStatus.ERROR
                    return False
            
            # Start streaming thread
            self.is_running = True
            self.start_time = time.time()
            self.stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.stream_thread.start()
            
            logger.info(f"[CAMERA_{self.camera_id}] Camera started successfully")
            return True
            
        except Exception as e:
            logger.error(f"[CAMERA_{self.camera_id}] Error starting camera: {e}")
            self.status = CameraStatus.ERROR
            self.error_count += 1
            return False
    
    def stop_camera(self):
        """Stop the camera stream"""
        if not self.is_running:
            return
        
        logger.info(f"[CAMERA_{self.camera_id}] Stopping camera")
        self.is_running = False
        
        # Wait for stream thread to finish
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2)
        
        # Release camera
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.status = CameraStatus.DISCONNECTED
        logger.info(f"[CAMERA_{self.camera_id}] Camera stopped")
    
    def _stream_loop(self):
        """Main camera streaming loop"""
        logger.info(f"[CAMERA_{self.camera_id}] Stream loop started")
        
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if ret:
                    with self.frame_lock:
                        self.latest_frame = frame.copy()
                        self.frame_count += 1
                    
                    # Call frame callback if provided
                    if self.frame_callback:
                        self.frame_callback(self.camera_id, frame)
                else:
                    logger.warning(f"[CAMERA_{self.camera_id}] Failed to read frame")
                    self.error_count += 1
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"[CAMERA_{self.camera_id}] Error in stream loop: {e}")
                self.error_count += 1
                time.sleep(0.1)
        
        logger.info(f"[CAMERA_{self.camera_id}] Stream loop ended")
    
    def get_latest_frame(self) -> Optional[object]:
        """Get the latest frame from camera"""
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None
    
    def get_status(self) -> Dict:
        """Get camera status information"""
        return {
            "camera_id": self.camera_id,
            "status": self.status.value,
            "is_running": self.is_running,
            "frame_count": self.frame_count,
            "error_count": self.error_count,
            "uptime": time.time() - self.start_time if self.start_time else 0
        }
    
    def is_available(self) -> bool:
        """Check if camera is available and running"""
        return self.is_running and self.status == CameraStatus.CONNECTED

class MultiCameraManager:
    """
    Simple multi-camera manager
    Manages multiple cameras and handles frame callbacks
    """
    
    def __init__(self, frame_callback: Optional[Callable] = None, mqtt_client=None):
        self.frame_callback = frame_callback
        self.mqtt_client = mqtt_client
        
        # Camera management
        self.cameras = {}
        self.available_cameras = []
        
        # Initialize available cameras
        self._initialize_cameras()
        
        logger.info(f"[MULTI_CAMERA] Initialized with {len(self.available_cameras)} cameras")
    
    def _initialize_cameras(self):
        """Initialize available cameras"""
        self.available_cameras = detect_available_cameras()
        
        for camera_id in self.available_cameras:
            self.cameras[camera_id] = Camera(
                camera_id=camera_id,
                frame_callback=self._on_frame_received
            )
    
    def _on_frame_received(self, camera_id: int, frame):
        """Handle frame received from camera"""
        try:
            # Call external frame callback if provided
            if self.frame_callback:
                self.frame_callback(camera_id, frame)
        except Exception as e:
            logger.error(f"[MULTI_CAMERA] Error in frame callback: {e}")
    
    def start_camera(self, camera_id: int) -> bool:
        """Start a specific camera"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].start_camera()
        return False
    
    def stop_camera(self, camera_id: int):
        """Stop a specific camera"""
        if camera_id in self.cameras:
            self.cameras[camera_id].stop_camera()
    
    def start_all_cameras(self) -> Dict[int, bool]:
        """Start all available cameras"""
        results = {}
        for camera_id in self.available_cameras:
            results[camera_id] = self.start_camera(camera_id)
        return results
    
    def stop_all_cameras(self):
        """Stop all cameras"""
        for camera_id in self.available_cameras:
            self.stop_camera(camera_id)
    
    def get_camera_count(self) -> int:
        """Get total number of cameras"""
        return len(self.available_cameras)
    
    def get_available_cameras(self) -> List[int]:
        """Get list of available camera IDs"""
        return self.available_cameras.copy()
    
    def get_camera_status(self, camera_id: int) -> Dict:
        """Get status of a specific camera"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_status()
        return {"error": "Camera not found"}
    
    def get_all_camera_status(self) -> Dict:
        """Get status of all cameras"""
        status = {}
        for camera_id in self.available_cameras:
            status[camera_id] = self.get_camera_status(camera_id)
        return status
    
    def get_latest_frame(self, camera_id: int) -> Optional[object]:
        """Get latest frame from a specific camera"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_latest_frame()
        return None