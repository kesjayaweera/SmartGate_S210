#!/usr/bin/env python3
"""
Enhanced Reverse Tunnel Manager for SmartGate
Supports multiple camera streams and comprehensive debugging
Handles multiple gates with multiple cameras each
"""

import subprocess
import threading
import time
import logging
import os
import glob
from typing import Dict, List, Optional, Callable

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReverseTunnelManager:
    """
    Enhanced reverse tunnel manager for multiple camera streams
    Supports multiple gates with multiple cameras each
    """
    
    def __init__(self, ec2_ip: str, ec2_user: str = "admin", 
                 local_base_port: int = 8080, remote_base_port: int = 8001,
                 ssh_key_path: Optional[str] = None, mqtt_client=None):
        self.ec2_ip = ec2_ip
        self.ec2_user = ec2_user
        self.local_base_port = local_base_port
        self.remote_base_port = remote_base_port
        self.ssh_key_path = ssh_key_path or self._find_ssh_key()
        self.mqtt_client = mqtt_client
        
        # Tunnel management
        self.tunnels: Dict[str, subprocess.Popen] = {}
        self.tunnel_status: Dict[str, bool] = {}
        self.tunnel_threads: Dict[str, threading.Thread] = {}
        self.is_running = False
        
        # Debugging and monitoring
        self.debug_callback: Optional[Callable] = None
        self.last_health_check = 0
        self.health_check_interval = 30  # seconds
        
        logger.info(f"[TUNNEL] Initialized for {ec2_user}@{ec2_ip}")
        logger.info(f"[TUNNEL] SSH Key: {self.ssh_key_path}")
        logger.info(f"[TUNNEL] Base ports - Local: {local_base_port}, Remote: {remote_base_port}")
    
    def _find_ssh_key(self) -> Optional[str]:
        """Find SSH key file in current directory"""
        possible_keys = [
            "UvicornServerAWS",
            "GateKey.pem", 
            "smartgate-key.pem",
            "ec2-key.pem",
            "key.pem"
        ]
        
        # Check for exact matches first
        for key_file in possible_keys:
            if os.path.exists(key_file):
                logger.info(f"[TUNNEL] Found SSH key: {key_file}")
                return key_file
        
        # Check for .pem files
        pem_files = glob.glob("*.pem")
        if pem_files:
            key_file = pem_files[0]
            logger.info(f"[TUNNEL] Found SSH key: {key_file}")
            return key_file
        
        logger.warning("[TUNNEL] No SSH key file found")
        return None
    
    def set_debug_callback(self, callback: Callable):
        """Set callback for debug messages"""
        self.debug_callback = callback
    
    def _send_debug_message(self, message: str, level: str = "INFO"):
        """Send debug message to callback and log"""
        logger.log(getattr(logging, level), f"[TUNNEL] {message}")
        if self.debug_callback:
            try:
                self.debug_callback(f"[TUNNEL] {message}", level)
            except Exception as e:
                logger.error(f"[TUNNEL] Error in debug callback: {e}")
    
    def _send_tunnel_status_to_dashboard(self, tunnel_name: str, status: bool, error: str = None):
        """Send tunnel status to dashboard via MQTT"""
        if not self.mqtt_client:
            return
        
        try:
            import json
            status_data = {
                "device_id": "smartgate_device_001",
                "tunnel_name": tunnel_name,
                "status": "connected" if status else "disconnected",
                "error": error,
                "timestamp": time.time()
            }
            
            topic = f"smartgate/tunnel_{tunnel_name}_status"
            json_data = json.dumps(status_data)
            
            if hasattr(self.mqtt_client, 'publish'):
                self.mqtt_client.publish(topic, json_data)
            elif hasattr(self.mqtt_client, 'client'):
                self.mqtt_client.client.publish(topic, json_data)
                
        except Exception as e:
            logger.error(f"[TUNNEL] Error sending tunnel status to dashboard: {e}")
    
    def start_tunnel(self, tunnel_name: str, local_port: int, remote_port: int) -> bool:
        """
        Start a reverse tunnel for a specific camera stream
        
        Args:
            tunnel_name: Unique name for this tunnel (e.g., "camera_0", "camera_1")
            local_port: Local port on Jetson Nano
            remote_port: Remote port on EC2 instance
        """
        if tunnel_name in self.tunnels:
            logger.warning(f"[TUNNEL] Tunnel {tunnel_name} already exists")
            return self.tunnel_status.get(tunnel_name, False)
        
        if not self.ssh_key_path:
            error_msg = "No SSH key file found"
            self._send_debug_message(f"Failed to start tunnel {tunnel_name}: {error_msg}", "ERROR")
            self._send_tunnel_status_to_dashboard(tunnel_name, False, error_msg)
            return False
        
        try:
            # Set proper permissions on SSH key
            os.chmod(self.ssh_key_path, 0o600)
            
            # Build SSH command
            ssh_cmd = [
                "ssh", "-N", "-R", f"0.0.0.0:{remote_port}:localhost:{local_port}",
                f"{self.ec2_user}@{self.ec2_ip}",
                "-i", self.ssh_key_path,
                "-o", "ServerAliveInterval=30",
                "-o", "ServerAliveCountMax=3", 
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null",
                "-o", "LogLevel=ERROR",
                "-o", "ExitOnForwardFailure=yes"
            ]
            
            self._send_debug_message(f"Starting tunnel {tunnel_name}: {local_port} -> {remote_port}")
            
            # Start tunnel process
            process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.tunnels[tunnel_name] = process
            self.tunnel_status[tunnel_name] = True
            
            # Start monitoring thread for this tunnel
            monitor_thread = threading.Thread(
                target=self._monitor_tunnel,
                args=(tunnel_name, process),
                daemon=True
            )
            monitor_thread.start()
            self.tunnel_threads[tunnel_name] = monitor_thread
            
            self._send_debug_message(f"Tunnel {tunnel_name} started successfully")
            self._send_tunnel_status_to_dashboard(tunnel_name, True)
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to start tunnel {tunnel_name}: {e}"
            self._send_debug_message(error_msg, "ERROR")
            self._send_tunnel_status_to_dashboard(tunnel_name, False, str(e))
            return False
    
    def _monitor_tunnel(self, tunnel_name: str, process: subprocess.Popen):
        """Monitor a tunnel process"""
        self._send_debug_message(f"Monitoring tunnel {tunnel_name}")
        
        try:
            # Wait for process to complete
            stdout, stderr = process.communicate()
            
            # Process ended
            if process.returncode == 0:
                self._send_debug_message(f"Tunnel {tunnel_name} closed normally")
            else:
                error_msg = f"Tunnel {tunnel_name} failed with code {process.returncode}"
                if stderr:
                    error_msg += f": {stderr}"
                self._send_debug_message(error_msg, "ERROR")
            
            # Update status
            self.tunnel_status[tunnel_name] = False
            self._send_tunnel_status_to_dashboard(tunnel_name, False, error_msg if process.returncode != 0 else None)
            
        except Exception as e:
            error_msg = f"Error monitoring tunnel {tunnel_name}: {e}"
            self._send_debug_message(error_msg, "ERROR")
            self.tunnel_status[tunnel_name] = False
            self._send_tunnel_status_to_dashboard(tunnel_name, False, str(e))
    
    def stop_tunnel(self, tunnel_name: str):
        """Stop a specific tunnel"""
        if tunnel_name not in self.tunnels:
            logger.warning(f"[TUNNEL] Tunnel {tunnel_name} not found")
            return
        
        try:
            process = self.tunnels[tunnel_name]
            if process.poll() is None:  # Process is still running
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            
            # Clean up
            del self.tunnels[tunnel_name]
            self.tunnel_status[tunnel_name] = False
            
            if tunnel_name in self.tunnel_threads:
                del self.tunnel_threads[tunnel_name]
            
            self._send_debug_message(f"Tunnel {tunnel_name} stopped")
            self._send_tunnel_status_to_dashboard(tunnel_name, False)
            
        except Exception as e:
            self._send_debug_message(f"Error stopping tunnel {tunnel_name}: {e}", "ERROR")
    
    def start_camera_tunnels(self, camera_ports: List[int]) -> Dict[int, bool]:
        """
        Start tunnels for multiple cameras
        
        Args:
            camera_ports: List of camera IDs (e.g., [0, 1] for cam0, cam1)
        
        Returns:
            Dict mapping camera_id to success status
        """
        results = {}
        
        for camera_id in camera_ports:
            tunnel_name = f"camera_{camera_id}"
            local_port = self.local_base_port + camera_id
            remote_port = self.remote_base_port + camera_id
            
            success = self.start_tunnel(tunnel_name, local_port, remote_port)
            results[camera_id] = success
            
            if success:
                time.sleep(1)  # Small delay between tunnel starts
        
        self.is_running = any(results.values())
        return results
    
    def stop_all_tunnels(self):
        """Stop all tunnels"""
        self._send_debug_message("Stopping all tunnels...")
        
        for tunnel_name in list(self.tunnels.keys()):
            self.stop_tunnel(tunnel_name)
        
        self.is_running = False
        self._send_debug_message("All tunnels stopped")
    
    def get_tunnel_status(self, tunnel_name: str) -> bool:
        """Get status of a specific tunnel"""
        return self.tunnel_status.get(tunnel_name, False)
    
    def get_all_tunnel_status(self) -> Dict[str, bool]:
        """Get status of all tunnels"""
        return self.tunnel_status.copy()
    
    def get_tunnel_count(self) -> int:
        """Get number of active tunnels"""
        return len([status for status in self.tunnel_status.values() if status])
    
    def health_check(self) -> Dict:
        """Perform health check on all tunnels"""
        current_time = time.time()
        
        # Only run health check if enough time has passed
        if current_time - self.last_health_check < self.health_check_interval:
            return {"status": "skipped", "reason": "too_soon"}
        
        self.last_health_check = current_time
        
        health_status = {
            "timestamp": current_time,
            "total_tunnels": len(self.tunnels),
            "active_tunnels": 0,
            "tunnel_details": {}
        }
        
        for tunnel_name, process in self.tunnels.items():
            is_running = process.poll() is None
            health_status["tunnel_details"][tunnel_name] = {
                "running": is_running,
                "return_code": process.returncode if not is_running else None
            }
            
            if is_running:
                health_status["active_tunnels"] += 1
            else:
                # Tunnel died, update status
                self.tunnel_status[tunnel_name] = False
                self._send_debug_message(f"Tunnel {tunnel_name} health check failed", "WARNING")
        
        # Send health status to dashboard
        if self.mqtt_client:
            try:
                import json
                health_data = {
                    "device_id": "smartgate_device_001",
                    "health_check": health_status,
                    "timestamp": current_time
                }
                
                topic = "smartgate/tunnel_health"
                json_data = json.dumps(health_data)
                
                if hasattr(self.mqtt_client, 'publish'):
                    self.mqtt_client.publish(topic, json_data)
                elif hasattr(self.mqtt_client, 'client'):
                    self.mqtt_client.client.publish(topic, json_data)
                    
            except Exception as e:
                logger.error(f"[TUNNEL] Error sending health status: {e}")
        
        return health_status
    
    def get_tunnel_urls(self, camera_ports: List[int]) -> Dict[int, str]:
        """Get tunnel URLs for cameras"""
        urls = {}
        for camera_id in camera_ports:
            remote_port = self.remote_base_port + camera_id
            urls[camera_id] = f"http://{self.ec2_ip}:{remote_port}/stream"
        return urls

# Global tunnel manager instance
tunnel_manager: Optional[ReverseTunnelManager] = None

def initialize_tunnel_manager(ec2_ip: str, ec2_user: str = "admin", 
                            local_base_port: int = 8080, remote_base_port: int = 8001,
                            ssh_key_path: Optional[str] = None, mqtt_client=None) -> ReverseTunnelManager:
    """Initialize the global tunnel manager"""
    global tunnel_manager
    tunnel_manager = ReverseTunnelManager(
        ec2_ip, ec2_user, local_base_port, remote_base_port, ssh_key_path, mqtt_client
    )
    return tunnel_manager

def get_tunnel_manager() -> Optional[ReverseTunnelManager]:
    """Get the global tunnel manager instance"""
    return tunnel_manager

def main():
    """Test function for tunnel manager"""
    print("Testing Reverse Tunnel Manager...")
    
    # Test tunnel manager
    manager = ReverseTunnelManager(
        ec2_ip="3.27.77.237",
        ec2_user="admin",
        local_base_port=8080,
        remote_base_port=8001
    )
    
    # Test starting camera tunnels
    camera_ports = [0, 1]
    results = manager.start_camera_tunnels(camera_ports)
    
    print(f"Tunnel start results: {results}")
    
    # Wait a bit
    time.sleep(5)
    
    # Health check
    health = manager.health_check()
    print(f"Health check: {health}")
    
    # Get URLs
    urls = manager.get_tunnel_urls(camera_ports)
    print(f"Tunnel URLs: {urls}")
    
    # Stop tunnels
    manager.stop_all_tunnels()
    print("Tunnels stopped")

if __name__ == "__main__":
    main()