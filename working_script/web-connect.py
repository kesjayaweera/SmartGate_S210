#!/usr/bin/env python3
"""
SmartGate Web Connect - Modular Version
Main integration script using modular components
"""

import sys
import os
import logging
import time

# Add gate_control module to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'gate_control'))

# Import modular components
from gate_control import SystemManager, ConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function"""
    print("=" * 60)
    print("SMARTGATE WEB CONNECT - MODULAR SYSTEM")
    print("=" * 60)
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        
        # Validate configuration
        if not config_manager.validate_config():
            logger.error("Configuration validation failed")
            return
        
        # Get configuration values
        mqtt_config = config_manager.get_mqtt_config()
        detection_config = config_manager.get_detection_config()
        system_config = config_manager.get_system_config()
        
        # Initialize system manager
        system_manager = SystemManager(
            broker_ip=mqtt_config["broker_ip"],
            broker_port=mqtt_config["broker_port"],
            device_id=mqtt_config["device_id"]
        )
        
        # Initialize system components
        logger.info("Initializing system components...")
        if not system_manager.initialize_system():
            logger.error("Failed to initialize system components")
            return
        
        # Connect to MQTT broker
        logger.info(f"Connecting to MQTT broker {mqtt_config['broker_ip']}:{mqtt_config['broker_port']}...")
        if not system_manager.connect():
            logger.error("Failed to connect to MQTT broker")
            return
        
        # Detection engine is handled by the camera manager
        logger.info("Detection engine will be initialized by camera manager if needed")
        
        # Start camera streams
        logger.info("Starting camera streams...")
        system_manager.is_running = True
        
        if system_manager.start_camera_streams():
            logger.info("Camera streams started successfully")
        else:
            logger.warning("Camera streams failed to start")
        
        # Send initial status
        system_manager._send_system_status()
        
        # Print system information
        system_info = system_manager.get_system_info()
        logger.info("System Information:")
        logger.info(f"  Device ID: {system_info['device_id']}")
        logger.info(f"  MQTT Connected: {system_info['mqtt_connected']}")
        logger.info(f"  Gate Control Available: {system_info['gate_available']}")
        logger.info(f"  Camera System Available: {system_info['camera_available']}")
        logger.info(f"  Detection Engine Available: {system_info['detection_available']}")
        
        # Run main system loop
        system_manager.run()
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        # Cleanup
        logger.info("Cleaning up...")
        if 'system_manager' in locals():
            system_manager.shutdown()
        logger.info("Cleanup complete")

if __name__ == "__main__":
    main()
