#!/usr/bin/env python3
"""
SmartGate Gate Control Package
Modular components for SmartGate system management
"""

from .mqtt_client import SmartGateMQTTClient
from .gate_controller import GateController
from .camera_manager import CameraManager
from .system_manager import SystemManager
from .config_manager import ConfigManager

__all__ = [
    'SmartGateMQTTClient',
    'GateController', 
    'CameraManager',
    'SystemManager',
    'ConfigManager'
]

__version__ = "1.0.0"
__author__ = "SmartGate Team"
__description__ = "Modular SmartGate control system"

