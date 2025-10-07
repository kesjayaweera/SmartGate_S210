#!/usr/bin/env python3
"""
SmartGate Camera Manager Module
Simple camera and tunnel management
"""

import os
import sys
import logging
from typing import Optional, Dict, List, Any

# Add camera and tunnel modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'camera'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'tunnel'))

logger = logging.getLogger(__name__)

class CameraManager:
    """
    Simple camera manager for SmartGate
    Handles camera streams, tunnels, and detection integration
    """
    
    def __init__(self, mqtt_client=None, detection_engine=None):
        self.mqtt_client = mqtt_client
        self.detection_engine = detection_engine
        
        # Camera and tunnel system
        self.camera_tunnel = None
        self.cameras_initialized = False
        self.streams_running = False
        
        # Configuration - simple defaults
        self.ec2_ip = "3.27.77.237"
        self.ec2_user = "admin"
        self.local_base_port = 8080
        self.remote_base_port = 8001
        
        logger.info("[CAMERA] Camera manager initialized")
    
    def _find_ssh_key(self) -> Optional[str]:
        """Find SSH key file - check common locations"""
        # Check tunnel folder first
        tunnel_key_path = os.path.join("tunnel", "UvicornServerAWS")
        if os.path.exists(tunnel_key_path):
            os.chmod(tunnel_key_path, 0o600)
            return tunnel_key_path
        
        # Check other common locations
        common_paths = ["UvicornServerAWS", "../tunnel/UvicornServerAWS"]
        for path in common_paths:
            if os.path.exists(path):
                os.chmod(path, 0o600)
                return path
        
        return None
    
    def _initialize_detection_engine(self):
        """Initialize detection engine using existing YoloDetTRT system"""
        try:
            # Import YoloDetTRT from parent directory
            parent_dir = os.path.dirname(os.path.dirname(__file__))
            sys.path.append(parent_dir)
            
            from YoloDetTRT import YoloTRT
            
            # Load configuration (this should ideally come from ConfigManager)
            config = {
                'path': 'models/yolov5s.engine',
                'classes': 'models/classes/marsupial16s.txt',
                'confidence': 0.5
            }
            
            # Initialize YoloTRT
            detection_engine = YoloTRT(config)
            
            if self.mqtt_client:
                self.mqtt_client.add_debug_message("Detection engine initialized successfully", "SUCCESS")
            
            logger.info("[CAMERA] Detection engine initialized with YoloDetTRT")
            return detection_engine
            
        except Exception as e:
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(f"Detection engine initialization failed: {e}", "WARNING")
            logger.warning(f"[CAMERA] Detection engine initialization failed: {e}")
            return None
    
    def initialize_cameras(self) -> bool:
        """Initialize camera and tunnel systems"""
        try:
            if self.mqtt_client:
                self.mqtt_client.add_debug_message("Initializing camera and tunnel systems...")
            
            # Find SSH key
            ssh_key = self._find_ssh_key()
            if not ssh_key:
                if self.mqtt_client:
                    self.mqtt_client.add_debug_message("No SSH key found - tunnel may fail", "WARNING")
            
            # Initialize detection engine if available
            detection_engine = self._initialize_detection_engine()
            
            # Import and initialize camera tunnel system
            from tunnel.camera_tunnel_code import initialize_camera_tunnel
            
            self.camera_tunnel = initialize_camera_tunnel(
                ec2_ip=self.ec2_ip,
                ec2_user=self.ec2_user,
                local_base_port=self.local_base_port,
                remote_base_port=self.remote_base_port,
                ssh_key_path=ssh_key,
                mqtt_client=self.mqtt_client,
                detection_engine=detection_engine  # Pass the initialized detection engine
            )
            
            self.cameras_initialized = True
            
            if self.mqtt_client:
                self.mqtt_client.add_debug_message("Camera and tunnel systems initialized", "SUCCESS")
            
            logger.info("[CAMERA] Camera and tunnel systems initialized")
            return True
            
        except Exception as e:
            error_msg = f"Error initializing cameras: {e}"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            logger.error(f"[CAMERA] {error_msg}")
            return False
    
    def start_camera_streams(self, camera_ids: List[int] = None) -> bool:
        """Start camera streams"""
        if not self.cameras_initialized:
            error_msg = "Cameras not initialized"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            return False
        
        try:
            if self.mqtt_client:
                self.mqtt_client.add_debug_message("Starting camera streams...")
            
            # Use default camera IDs if none provided
            if camera_ids is None:
                camera_ids = [0, 1]  # Default to cameras 0 and 1
            
            # Start camera streams through tunnel system
            if self.camera_tunnel:
                self.camera_tunnel.start_camera_streams(camera_ids)
                self.streams_running = True
                
                success_msg = f"Camera streams started for cameras: {camera_ids}"
                if self.mqtt_client:
                    self.mqtt_client.add_debug_message(success_msg, "SUCCESS")
                
                logger.info(f"[CAMERA] {success_msg}")
                return True
            else:
                error_msg = "Camera tunnel not available"
                if self.mqtt_client:
                    self.mqtt_client.add_debug_message(error_msg, "ERROR")
                return False
                
        except Exception as e:
            error_msg = f"Error starting camera streams: {e}"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            logger.error(f"[CAMERA] {error_msg}")
            return False
    
    def stop_camera_streams(self) -> bool:
        """Stop camera streams"""
        try:
            if self.mqtt_client:
                self.mqtt_client.add_debug_message("Stopping camera streams...")
            
            if self.camera_tunnel:
                self.camera_tunnel.stop_camera_streams()
                self.streams_running = False
                
                success_msg = "Camera streams stopped"
                if self.mqtt_client:
                    self.mqtt_client.add_debug_message(success_msg, "SUCCESS")
                
                logger.info(f"[CAMERA] {success_msg}")
                return True
            else:
                error_msg = "Camera tunnel not available"
                if self.mqtt_client:
                    self.mqtt_client.add_debug_message(error_msg, "ERROR")
                return False
                
        except Exception as e:
            error_msg = f"Error stopping camera streams: {e}"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            logger.error(f"[CAMERA] {error_msg}")
            return False
    
    def get_camera_status(self) -> Dict[str, Any]:
        """Get camera system status"""
        return {
            "cameras_initialized": self.cameras_initialized,
            "streams_running": self.streams_running,
            "tunnel_available": self.camera_tunnel is not None,
            "detection_available": self.detection_engine is not None
        }
    
    def handle_mqtt_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle MQTT camera commands"""
        if params is None:
            params = {}
        
        command = command.upper()
        
        # Route commands to appropriate methods
        if command == "START_CAMERA":
            camera_ids = params.get("camera_ids", [0, 1])
            success = self.start_camera_streams(camera_ids)
            return {"success": success, "message": "Camera streams started" if success else "Failed to start camera streams"}
        
        elif command == "STOP_CAMERA":
            success = self.stop_camera_streams()
            return {"success": success, "message": "Camera streams stopped" if success else "Failed to stop camera streams"}
        
        elif command == "GET_CAMERA_STATUS":
            status = self.get_camera_status()
            return {"success": True, "message": "Camera status retrieved", "status": status}
        
        else:
            error_msg = f"Unknown camera command: {command}"
            if self.mqtt_client:
                self.mqtt_client.add_debug_message(error_msg, "ERROR")
            
            return {"success": False, "message": error_msg, "error": error_msg}