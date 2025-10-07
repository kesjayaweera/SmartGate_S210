#!/usr/bin/env python3
"""
Simple Camera Tunnel Integration Code
Integrates multi-camera system with reverse tunnel for dashboard streaming
"""

import cv2
import threading
import time
import logging
import json
from typing import Optional, Callable, Dict, List
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

# Import our camera and tunnel systems
import sys
import os

# Add camera directory to path
camera_dir = os.path.join(os.path.dirname(__file__), '..', 'camera')
if camera_dir not in sys.path:
    sys.path.insert(0, camera_dir)

from camera_script import MultiCameraManager, Camera
from reverse_tunnel import ReverseTunnelManager

logger = logging.getLogger(__name__)

class CameraStreamHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for camera streams"""
    
    def __init__(self, camera_manager, *args, **kwargs):
        self.camera_manager = camera_manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests - simple routing"""
        if self.path == '/stream':
            self.handle_camera_stream()
        elif self.path.startswith('/stream/'):
            # Handle specific camera stream: /stream/0, /stream/1
            try:
                camera_id = int(self.path.split('/')[-1])
                self.handle_specific_camera_stream(camera_id)
            except ValueError:
                self.send_error(400, "Invalid camera ID")
        elif self.path == '/status':
            self.handle_status_request()
        else:
            self.send_error(404, "Not Found")
    
    def handle_camera_stream(self):
        """Handle main camera stream request"""
        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        
        try:
            while True:
                # Get frame from first available camera
                for camera_id in self.camera_manager.get_available_cameras():
                    frame = self.camera_manager.get_latest_frame(camera_id)
                    if frame is not None:
                        _, jpeg = cv2.imencode('.jpg', frame)
                        self.wfile.write(b'--frame\r\n')
                        self.send_header('Content-type', 'image/jpeg')
                        self.send_header('Content-length', len(jpeg))
                        self.end_headers()
                        self.wfile.write(jpeg.tobytes())
                        self.wfile.write(b'\r\n')
                        break
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"[STREAM] Error in camera stream: {e}")
    
    def handle_specific_camera_stream(self, camera_id: int):
        """Handle specific camera stream request"""
        if camera_id not in self.camera_manager.get_available_cameras():
            self.send_error(404, "Camera not found")
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        
        try:
            while True:
                frame = self.camera_manager.get_latest_frame(camera_id)
                if frame is not None:
                    _, jpeg = cv2.imencode('.jpg', frame)
                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', len(jpeg))
                    self.end_headers()
                    self.wfile.write(jpeg.tobytes())
                    self.wfile.write(b'\r\n')
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"[STREAM] Error in camera {camera_id} stream: {e}")
    
    def handle_status_request(self):
        """Handle status request"""
        try:
            status = {
                "system_status": "running",
                "cameras": self.camera_manager.get_all_camera_status(),
                "timestamp": time.time()
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            json_data = json.dumps(status, default=str)
            self.wfile.write(json_data.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"[STATUS] Error handling status request: {e}")
            self.send_error(500, f"Status error: {e}")
    
    def log_message(self, format, *args):
        """Override to reduce log noise"""
        pass

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Threaded HTTP server for handling multiple requests"""
    allow_reuse_address = True
    daemon_threads = True

class CameraTunnelCode:
    """
    Simple camera tunnel integration
    Handles multiple cameras, detection engine integration, and dashboard streaming
    """
    
    def __init__(self, ec2_ip: str, ec2_user: str = "admin", 
                 local_base_port: int = 8080, remote_base_port: int = 8001,
                 ssh_key_path: Optional[str] = None, mqtt_client=None,
                 detection_engine=None):
        
        self.ec2_ip = ec2_ip
        self.ec2_user = ec2_user
        self.local_base_port = local_base_port
        self.remote_base_port = remote_base_port
        self.ssh_key_path = ssh_key_path
        self.mqtt_client = mqtt_client
        self.detection_engine = detection_engine
        
        # Initialize camera manager
        self.camera_manager = MultiCameraManager(
            frame_callback=self._on_frame_received,
            mqtt_client=mqtt_client
        )
        
        # Initialize tunnel manager
        self.tunnel_manager = ReverseTunnelManager(
            ec2_ip=ec2_ip,
            ec2_user=ec2_user,
            local_base_port=local_base_port,
            remote_base_port=remote_base_port,
            ssh_key_path=ssh_key_path,
            mqtt_client=mqtt_client
        )
        
        # HTTP server
        self.http_server = None
        self.server_thread = None
        self.is_running = False
        
        # Statistics
        self.start_time = None
        self.frame_count = 0
        self.detection_count = 0
        
        logger.info("[CAMERA_TUNNEL] Initialized")
    
    def _on_frame_received(self, camera_id: int, frame):
        """Handle frame received from camera"""
        try:
            self.frame_count += 1
            
            # Send frame to detection engine if available
            if self.detection_engine and hasattr(self.detection_engine, 'detect'):
                try:
                    detections = self.detection_engine.detect(frame)
                    if detections:
                        self.detection_count += 1
                        logger.info(f"[CAMERA_TUNNEL] Camera {camera_id}: {len(detections)} detections")
                except Exception as e:
                    logger.error(f"[CAMERA_TUNNEL] Error in detection engine: {e}")
        except Exception as e:
            logger.error(f"[CAMERA_TUNNEL] Error handling frame: {e}")
    
    def start_http_server(self, port: int = 8080) -> bool:
        """Start HTTP server for camera streams"""
        try:
            logger.info(f"[CAMERA_TUNNEL] Starting HTTP server on port {port}")
            
            # Create handler with camera manager
            handler = lambda *args, **kwargs: CameraStreamHandler(self.camera_manager, *args, **kwargs)
            
            # Start server
            self.http_server = ThreadedHTTPServer(('0.0.0.0', port), handler)
            self.server_thread = threading.Thread(target=self.http_server.serve_forever, daemon=True)
            self.server_thread.start()
            
            logger.info(f"[CAMERA_TUNNEL] HTTP server started on port {port}")
            return True
            
        except Exception as e:
            logger.error(f"[CAMERA_TUNNEL] Error starting HTTP server: {e}")
            return False
    
    def stop_http_server(self):
        """Stop HTTP server"""
        if self.http_server:
            logger.info("[CAMERA_TUNNEL] Stopping HTTP server")
            self.http_server.shutdown()
            self.http_server = None
    
    def start_camera_streams(self, camera_ids: List[int] = [0, 1]) -> Dict[int, bool]:
        """Start camera streams and tunnels"""
        try:
            logger.info(f"[CAMERA_TUNNEL] Starting camera streams for cameras: {camera_ids}")
            
            # Start HTTP server
            if not self.start_http_server(self.local_base_port):
                return {camera_id: False for camera_id in camera_ids}
            
            # Start cameras
            camera_results = {}
            for camera_id in camera_ids:
                if camera_id in self.camera_manager.get_available_cameras():
                    camera_results[camera_id] = self.camera_manager.start_camera(camera_id)
                else:
                    camera_results[camera_id] = False
            
            # Start tunnels for each camera
            tunnel_results = {}
            for camera_id in camera_ids:
                if camera_results.get(camera_id, False):
                    tunnel_name = f"camera_{camera_id}"
                    local_port = self.local_base_port + camera_id
                    remote_port = self.remote_base_port + camera_id
                    
                    tunnel_results[camera_id] = self.tunnel_manager.start_tunnel(
                        tunnel_name, local_port, remote_port
                    )
                else:
                    tunnel_results[camera_id] = False
            
            self.is_running = True
            self.start_time = time.time()
            
            logger.info(f"[CAMERA_TUNNEL] Camera streams started: {camera_results}")
            logger.info(f"[CAMERA_TUNNEL] Tunnels started: {tunnel_results}")
            
            return camera_results
            
        except Exception as e:
            logger.error(f"[CAMERA_TUNNEL] Error starting camera streams: {e}")
            return {camera_id: False for camera_id in camera_ids}
    
    def stop_camera_streams(self):
        """Stop camera streams and tunnels"""
        try:
            logger.info("[CAMERA_TUNNEL] Stopping camera streams")
            
            # Stop cameras
            self.camera_manager.stop_all_cameras()
            
            # Stop tunnels
            self.tunnel_manager.stop_all_tunnels()
            
            # Stop HTTP server
            self.stop_http_server()
            
            self.is_running = False
            logger.info("[CAMERA_TUNNEL] Camera streams stopped")
            
        except Exception as e:
            logger.error(f"[CAMERA_TUNNEL] Error stopping camera streams: {e}")
    
    def get_camera_status(self, camera_id: int) -> Dict:
        """Get status of a specific camera"""
        return self.camera_manager.get_camera_status(camera_id)
    
    def get_all_camera_status(self) -> Dict:
        """Get status of all cameras"""
        return self.camera_manager.get_all_camera_status()
    
    def get_tunnel_status(self) -> Dict:
        """Get tunnel status"""
        return self.tunnel_manager.get_tunnel_status()
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        return {
            "is_running": self.is_running,
            "cameras": self.get_all_camera_status(),
            "tunnels": self.get_tunnel_status(),
            "frame_count": self.frame_count,
            "detection_count": self.detection_count,
            "uptime": time.time() - self.start_time if self.start_time else 0
        }
    
    def get_stream_urls(self) -> Dict[int, str]:
        """Get stream URLs for all cameras"""
        urls = {}
        for camera_id in self.camera_manager.get_available_cameras():
            urls[camera_id] = f"http://localhost:{self.local_base_port}/stream/{camera_id}"
        return urls

def initialize_camera_tunnel(ec2_ip: str, ec2_user: str = "admin",
                           local_base_port: int = 8080, remote_base_port: int = 8001,
                           ssh_key_path: Optional[str] = None, mqtt_client=None,
                           detection_engine=None) -> CameraTunnelCode:
    """Initialize camera tunnel system"""
    return CameraTunnelCode(
        ec2_ip=ec2_ip,
        ec2_user=ec2_user,
        local_base_port=local_base_port,
        remote_base_port=remote_base_port,
        ssh_key_path=ssh_key_path,
        mqtt_client=mqtt_client,
        detection_engine=detection_engine
    )

def get_camera_tunnel() -> Optional[CameraTunnelCode]:
    """Get the global camera tunnel instance"""
    return getattr(get_camera_tunnel, '_instance', None)

def main():
    """Main function for testing"""
    # Initialize camera tunnel
    camera_tunnel = initialize_camera_tunnel(
        ec2_ip="3.27.77.237",
        ec2_user="admin",
        local_base_port=8080,
        remote_base_port=8001
    )
    
    try:
        # Start camera streams
        results = camera_tunnel.start_camera_streams([0, 1])
        print(f"Camera start results: {results}")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("Stopping camera tunnel...")
        camera_tunnel.stop_camera_streams()

if __name__ == "__main__":
    main()