#!/usr/bin/env python3
"""
SmartGate Bridge - Docker Container
Bridges between local SmartGate control interface and hosted server.
Maintains outbound connection to handle NAT traversal.
"""

import os
import sys
import time
import json
import yaml
import logging
import threading
import requests
import socket
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
import netifaces
import psutil
import colorlog

class SmartGateBridge:
    """Main bridge class that handles communication between gate and server."""
    
    def __init__(self):
        self.config = self._load_config()
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Connection state
        self.server_connected = False
        self.last_heartbeat = None
        self.connection_thread = None
        self.heartbeat_thread = None
        self.running = False
        
        # Flask app for local interface
        self.app = Flask(__name__)
        self.setup_flask_routes()
        
        # Device information
        self.device_info = self._get_device_info()
        
        self.logger.info("SmartGate Bridge initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file and environment variables."""
        load_dotenv()
        
        # Load YAML config
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Override with environment variables
        env_mappings = {
            'SERVER_HOST': ['server', 'host'],
            'SERVER_PORT': ['server', 'port'],
            'SERVER_ENDPOINT': ['server', 'endpoint'],
            'DEVICE_ID': ['device', 'device_id'],
            'DEVICE_NAME': ['device', 'name'],
            'LOCAL_PORT': ['gate', 'local_port'],
            'LOG_LEVEL': ['logging', 'level']
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                if config_path[1] in ['port']:
                    value = int(value)
                self._set_nested_config(config, config_path, value)
        
        return config
    
    def _set_nested_config(self, config: Dict, path: list, value: Any):
        """Set nested configuration value."""
        current = config
        for key in path[:-1]:
            current = current[key]
        current[path[-1]] = value
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config['logging']
        
        # Create logs directory
        log_dir = os.path.dirname(log_config['file'])
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, log_config['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_config['file']),
                logging.StreamHandler()
            ]
        )
        
        # Add colored console output
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(console_handler)
    
    def _get_device_info(self) -> Dict[str, Any]:
        """Get device information for registration."""
        try:
            # Get local IP address
            local_ip = self._get_local_ip()
            
            return {
                'device_id': self.config['device']['device_id'],
                'name': self.config['device']['name'],
                'location': self.config['device']['location'],
                'version': self.config['device']['version'],
                'local_ip': local_ip,
                'local_port': self.config['gate']['local_port'],
                'status': 'online',
                'last_seen': datetime.now().isoformat(),
                'capabilities': ['gate_control', 'status_monitoring', 'health_check']
            }
        except Exception as e:
            self.logger.error(f"Error getting device info: {e}")
            return {}
    
    def _get_local_ip(self) -> str:
        """Get the local IP address of the device."""
        try:
            # Try to get IP from default gateway interface
            gateways = netifaces.gateways()
            default_interface = gateways['default'][netifaces.AF_INET][1]
            addresses = netifaces.ifaddresses(default_interface)
            return addresses[netifaces.AF_INET][0]['addr']
        except:
            # Fallback to socket method
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            except:
                ip = "127.0.0.1"
            finally:
                s.close()
            return ip
    
    def setup_flask_routes(self):
        """Setup Flask routes for local gate interface."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'server_connected': self.server_connected,
                'device_info': self.device_info
            })
        
        @self.app.route('/status', methods=['GET'])
        def get_status():
            """Get gate status."""
            try:
                # This would interface with the actual SmartGate
                # For now, return mock status
                return jsonify({
                    'gate_status': 'closed',
                    'motion_detected': False,
                    'last_activity': datetime.now().isoformat(),
                    'server_connected': self.server_connected
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/control', methods=['POST'])
        def control_gate():
            """Control gate operations."""
            try:
                data = request.get_json()
                command = data.get('command')
                
                if command not in ['open', 'close', 'stop']:
                    return jsonify({'error': 'Invalid command'}), 400
                
                # Forward command to server
                self._forward_command_to_server(command, data)
                
                return jsonify({
                    'status': 'success',
                    'command': command,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/register', methods=['POST'])
        def register_device():
            """Register device with server."""
            try:
                success = self._register_with_server()
                return jsonify({
                    'status': 'success' if success else 'failed',
                    'device_info': self.device_info
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _register_with_server(self) -> bool:
        """Register device with the hosted server."""
        try:
            server_config = self.config['server']
            url = f"{server_config['protocol']}://{server_config['host']}:{server_config['port']}{server_config['endpoint']}"
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'SmartGate-Bridge/1.0',
                'X-API-Key': self.config['security']['api_key']
            }
            
            response = requests.post(
                url,
                json=self.device_info,
                headers=headers,
                timeout=self.config['server']['connection_timeout']
            )
            
            if response.status_code == 200:
                self.logger.info("Successfully registered with server")
                self.server_connected = True
                return True
            else:
                self.logger.error(f"Registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error registering with server: {e}")
            return False
    
    def _forward_command_to_server(self, command: str, data: Dict[str, Any]):
        """Forward gate control command to server."""
        try:
            server_config = self.config['server']
            url = f"{server_config['protocol']}://{server_config['host']}:{server_config['port']}/gate-command"
            
            payload = {
                'device_id': self.device_info['device_id'],
                'command': command,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.config['security']['api_key']
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.config['server']['connection_timeout']
            )
            
            if response.status_code == 200:
                self.logger.info(f"Command '{command}' forwarded to server successfully")
            else:
                self.logger.error(f"Failed to forward command: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error forwarding command to server: {e}")
    
    def _maintain_connection(self):
        """Maintain connection to server with automatic reconnection."""
        while self.running:
            try:
                if not self.server_connected:
                    self.logger.info("Attempting to connect to server...")
                    self._register_with_server()
                
                time.sleep(self.config['server']['reconnect_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in connection maintenance: {e}")
                self.server_connected = False
                time.sleep(5)
    
    def _send_heartbeat(self):
        """Send periodic heartbeat to server."""
        while self.running:
            try:
                if self.server_connected:
                    server_config = self.config['server']
                    url = f"{server_config['protocol']}://{server_config['host']}:{server_config['port']}/heartbeat"
                    
                    payload = {
                        'device_id': self.device_info['device_id'],
                        'timestamp': datetime.now().isoformat(),
                        'status': 'online'
                    }
                    
                    headers = {
                        'Content-Type': 'application/json',
                        'X-API-Key': self.config['security']['api_key']
                    }
                    
                    response = requests.post(
                        url,
                        json=payload,
                        headers=headers,
                        timeout=self.config['server']['connection_timeout']
                    )
                    
                    if response.status_code == 200:
                        self.last_heartbeat = datetime.now()
                        self.logger.debug("Heartbeat sent successfully")
                    else:
                        self.logger.warning(f"Heartbeat failed: {response.status_code}")
                        self.server_connected = False
                
                time.sleep(self.config['server']['heartbeat_interval'])
                
            except Exception as e:
                self.logger.error(f"Error sending heartbeat: {e}")
                self.server_connected = False
                time.sleep(10)
    
    def start(self):
        """Start the bridge service."""
        self.logger.info("Starting SmartGate Bridge...")
        self.running = True
        
        # Start connection maintenance thread
        self.connection_thread = threading.Thread(target=self._maintain_connection, daemon=True)
        self.connection_thread.start()
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._send_heartbeat, daemon=True)
        self.heartbeat_thread.start()
        
        # Start Flask app
        gate_config = self.config['gate']
        self.logger.info(f"Starting local interface on {gate_config['local_host']}:{gate_config['local_port']}")
        
        self.app.run(
            host=gate_config['local_host'],
            port=gate_config['local_port'],
            debug=False,
            threaded=True
        )
    
    def stop(self):
        """Stop the bridge service."""
        self.logger.info("Stopping SmartGate Bridge...")
        self.running = False
        
        if self.connection_thread:
            self.connection_thread.join(timeout=5)
        
        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=5)
        
        self.logger.info("SmartGate Bridge stopped")

def main():
    """Main entry point."""
    try:
        bridge = SmartGateBridge()
        
        # Handle graceful shutdown
        import signal
        def signal_handler(sig, frame):
            bridge.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        bridge.start()
        
    except KeyboardInterrupt:
        print("Received keyboard interrupt")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

