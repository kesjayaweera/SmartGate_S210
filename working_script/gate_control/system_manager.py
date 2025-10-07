#!/usr/bin/env python3
"""
SmartGate System Manager Module
Simple system orchestrator for all components
"""

import time
import logging
from typing import Optional, Dict, Any

from .mqtt_client import SmartGateMQTTClient
from .gate_controller import GateController
from .camera_manager import CameraManager

logger = logging.getLogger(__name__)

class SystemManager:
    """
    Simple system manager for SmartGate
    Orchestrates MQTT, gate control, camera management, and detection
    """
    
    def __init__(self, broker_ip: str, broker_port: int = 1883, device_id: str = "smartgate_device_001"):
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.device_id = device_id
        
        # System state
        self.is_running = False
        
        # Initialize components
        self.mqtt_client = None
        self.gate_controller = None
        self.camera_manager = None
        
        logger.info(f"[SYSTEM] System manager initialized for {broker_ip}:{broker_port}")
    
    def initialize_system(self) -> bool:
        """Initialize all system components"""
        try:
            logger.info("[SYSTEM] Initializing system components...")
            
            # Initialize MQTT client
            self.mqtt_client = SmartGateMQTTClient(
                broker_ip=self.broker_ip,
                broker_port=self.broker_port,
                device_id=self.device_id
            )
            
            # Initialize gate controller
            self.gate_controller = GateController(mqtt_client=self.mqtt_client)
            
            # Initialize camera manager (detection engine will be initialized internally)
            self.camera_manager = CameraManager(mqtt_client=self.mqtt_client)
            
            # Register MQTT callbacks
            self._register_mqtt_callbacks()
            
            logger.info("[SYSTEM] System components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"[SYSTEM] Error initializing system: {e}")
            return False
    
    def _register_mqtt_callbacks(self):
        """Register MQTT command callbacks - simple command routing"""
        if not self.mqtt_client:
            return
        
        # Register gate control callbacks
        self.mqtt_client.register_command_callback("OPEN_GATE", self._handle_gate_command)
        self.mqtt_client.register_command_callback("CLOSE_GATE", self._handle_gate_command)
        self.mqtt_client.register_command_callback("STOP_GATE", self._handle_gate_command)
        self.mqtt_client.register_command_callback("GET_STATUS", self._handle_gate_command)
        
        # Register camera control callbacks
        self.mqtt_client.register_command_callback("START_CAMERA", self._handle_camera_command)
        self.mqtt_client.register_command_callback("STOP_CAMERA", self._handle_camera_command)
        self.mqtt_client.register_command_callback("GET_CAMERA_STATUS", self._handle_camera_command)
        
        # Register system control callbacks
        self.mqtt_client.register_command_callback("INITIALIZE_CAMERAS", self._handle_initialize_cameras)
        self.mqtt_client.register_command_callback("GET_SYSTEM_STATUS", self._handle_get_system_status)
        
        logger.info("[SYSTEM] MQTT command callbacks registered")
    
    def _handle_gate_command(self, command: str, params: Dict[str, Any] = None):
        """Handle gate commands - route to gate controller"""
        if not self.gate_controller:
            logger.error("[SYSTEM] Gate controller not available")
            return
        
        try:
            result = self.gate_controller.handle_mqtt_command(command, params)
            logger.info(f"[SYSTEM] Gate command {command} result: {result}")
        except Exception as e:
            logger.error(f"[SYSTEM] Error handling gate command {command}: {e}")
    
    def _handle_camera_command(self, command: str, params: Dict[str, Any] = None):
        """Handle camera commands - route to camera manager"""
        if not self.camera_manager:
            logger.error("[SYSTEM] Camera manager not available")
            return
        
        try:
            result = self.camera_manager.handle_mqtt_command(command, params)
            logger.info(f"[SYSTEM] Camera command {command} result: {result}")
        except Exception as e:
            logger.error(f"[SYSTEM] Error handling camera command {command}: {e}")
    
    def _handle_initialize_cameras(self, command: str, params: Dict[str, Any] = None):
        """Handle camera initialization command"""
        if not self.camera_manager:
            logger.error("[SYSTEM] Camera manager not available")
            return
        
        try:
            success = self.camera_manager.initialize_cameras()
            if success:
                logger.info("[SYSTEM] Cameras initialized successfully")
            else:
                logger.error("[SYSTEM] Failed to initialize cameras")
        except Exception as e:
            logger.error(f"[SYSTEM] Error initializing cameras: {e}")
    
    def _handle_get_system_status(self, command: str, params: Dict[str, Any] = None):
        """Handle system status request"""
        try:
            status = {
                "system_running": self.is_running,
                "mqtt_connected": self.mqtt_client.is_connected if self.mqtt_client else False,
                "gate_available": self.gate_controller.is_available() if self.gate_controller else False,
                "cameras_initialized": self.camera_manager.cameras_initialized if self.camera_manager else False,
                "streams_running": self.camera_manager.streams_running if self.camera_manager else False
            }
            
            logger.info(f"[SYSTEM] System status: {status}")
            
            # Publish status via MQTT
            if self.mqtt_client:
                self.mqtt_client.publish_status(status)
                
        except Exception as e:
            logger.error(f"[SYSTEM] Error getting system status: {e}")
    
    def connect(self) -> bool:
        """Connect to MQTT broker"""
        if not self.mqtt_client:
            logger.error("[SYSTEM] MQTT client not initialized")
            return False
        
        return self.mqtt_client.connect()
    
    def start_camera_streams(self) -> bool:
        """Start camera streams"""
        if not self.camera_manager:
            logger.error("[SYSTEM] Camera manager not initialized")
            return False
        
        return self.camera_manager.start_camera_streams()
    
    def stop_camera_streams(self) -> bool:
        """Stop camera streams"""
        if not self.camera_manager:
            logger.error("[SYSTEM] Camera manager not initialized")
            return False
        
        return self.camera_manager.stop_camera_streams()
    
    def start_system(self) -> bool:
        """Start the complete system"""
        try:
            logger.info("[SYSTEM] Starting SmartGate system...")
            
            # Connect to MQTT broker
            if not self.connect():
                logger.error("[SYSTEM] Failed to connect to MQTT broker")
                return False
            
            # Initialize cameras
            if not self.camera_manager.initialize_cameras():
                logger.warning("[SYSTEM] Camera initialization failed, continuing without cameras")
            
            self.is_running = True
            logger.info("[SYSTEM] SmartGate system started successfully")
            return True
            
        except Exception as e:
            logger.error(f"[SYSTEM] Error starting system: {e}")
            return False
    
    def stop_system(self):
        """Stop the complete system"""
        try:
            logger.info("[SYSTEM] Stopping SmartGate system...")
            
            # Stop camera streams
            if self.camera_manager:
                self.camera_manager.stop_camera_streams()
            
            # Disconnect from MQTT
            if self.mqtt_client:
                self.mqtt_client.disconnect()
            
            self.is_running = False
            logger.info("[SYSTEM] SmartGate system stopped")
            
        except Exception as e:
            logger.error(f"[SYSTEM] Error stopping system: {e}")
    
    def run(self):
        """Main system loop - keep system running"""
        try:
            logger.info("[SYSTEM] Starting main system loop...")
            
            while self.is_running:
                # Keep the system alive and handle any periodic tasks
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("[SYSTEM] Keyboard interrupt received, stopping system...")
            self.stop_system()
        except Exception as e:
            logger.error(f"[SYSTEM] Error in main loop: {e}")
            self.stop_system()