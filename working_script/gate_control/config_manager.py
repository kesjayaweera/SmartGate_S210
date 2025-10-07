#!/usr/bin/env python3
"""
SmartGate Configuration Manager
Simple configuration loader with sensible defaults
"""

import json
import os
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Simple configuration manager for SmartGate
    Loads config from file or uses defaults
    """
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        # Default configuration - simple and clean
        self.config = {
            "mqtt": {
                "broker_ip": "3.27.77.237",
                "broker_port": 1883,
                "device_id": "smartgate_device_001"
            },
            "camera": {
                "ec2_ip": "3.27.77.237",
                "ec2_user": "admin",
                "local_base_port": 8080,
                "remote_base_port": 8001,
                "ssh_key_path": "tunnel/UvicornServerAWS"
            },
            "detection": {
                "enabled": True,
                "model_path": "models/yolov5s.engine",
                "confidence_threshold": 0.5,
                "classes": "models/classes/marsupial16s.txt"
            }
        }
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file if it exists"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    file_config = json.load(f)
                    # Merge file config with defaults
                    self._merge_config(file_config)
                logger.info(f"[CONFIG] Loaded from {self.config_file}")
            else:
                logger.info("[CONFIG] Using default configuration")
                self.save_config()  # Save defaults for future use
        except Exception as e:
            logger.error(f"[CONFIG] Error loading config: {e}")
    
    def _merge_config(self, file_config):
        """Merge file configuration with defaults"""
        for key, value in file_config.items():
            if key in self.config and isinstance(self.config[key], dict) and isinstance(value, dict):
                self.config[key].update(value)
            else:
                self.config[key] = value
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"[CONFIG] Saved to {self.config_file}")
        except Exception as e:
            logger.error(f"[CONFIG] Error saving config: {e}")
    
    def get(self, key_path: str, default=None):
        """Get configuration value by key path (e.g., 'mqtt.broker_ip')"""
        try:
            keys = key_path.split('.')
            value = self.config
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_mqtt_config(self):
        """Get MQTT configuration"""
        return self.config.get("mqtt", {})
    
    def get_camera_config(self):
        """Get camera configuration"""
        return self.config.get("camera", {})
    
    def get_detection_config(self):
        """Get detection configuration"""
        return self.config.get("detection", {})
    
    def validate_config(self) -> bool:
        """Validate that required configuration is present"""
        required_fields = [
            "mqtt.broker_ip",
            "mqtt.broker_port", 
            "mqtt.device_id",
            "camera.ec2_ip",
            "camera.ec2_user"
        ]
        
        for field in required_fields:
            if self.get(field) is None:
                logger.error(f"[CONFIG] Missing required field: {field}")
                return False
        
        logger.info("[CONFIG] Configuration validation passed")
        return True

