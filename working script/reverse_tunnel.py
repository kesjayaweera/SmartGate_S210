#!/usr/bin/env python3
"""
Reverse SSH Tunnel Manager for SmartGate
- Manages SSH reverse tunnel to EC2
- Handles tunnel reconnection
- Monitors tunnel health
"""

import subprocess
import threading
import time
import signal
import sys
import socket
import os

class ReverseTunnelManager:
    """Manages SSH reverse tunnel to EC2"""
    
    def __init__(self, ec2_ip, ec2_user="ubuntu", local_port=8080, remote_port=8001):
        self.ec2_ip = ec2_ip
        self.ec2_user = ec2_user
        self.local_port = local_port
        self.remote_port = remote_port
        self.tunnel_process = None
        self.is_running = False
        self.tunnel_thread = None
        self.health_check_interval = 30  # Check every 30 seconds
        
        print(f"[+] Reverse Tunnel Manager initialized")
        print(f"[+] Target: {ec2_user}@{ec2_ip}")
        print(f"[+] Tunnel: {remote_port}:localhost:{local_port}")
    
    def start_tunnel(self):
        """Start SSH reverse tunnel"""
        if self.is_running:
            print("[+] Reverse tunnel already running")
            return True
        
        try:
            print(f"[+] Starting reverse tunnel to {self.ec2_ip}...")
            
            # SSH command for reverse tunnel
            ssh_cmd = [
                "ssh", "-N", "-R", f"{self.remote_port}:localhost:{self.local_port}",
                f"{self.ec2_user}@{self.ec2_ip}",
                "-o", "ServerAliveInterval=30",
                "-o", "ServerAliveCountMax=3",
                "-o", "StrictHostKeyChecking=no",
                "-o", "UserKnownHostsFile=/dev/null"
            ]
            
            # Start tunnel process
            self.tunnel_process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=None
            )
            
            # Wait a moment for tunnel to establish
            time.sleep(3)
            
            # Check if tunnel started successfully
            if self.tunnel_process.poll() is None:
                self.is_running = True
                print(f"[+] Reverse tunnel started successfully")
                print(f"[+] Camera stream available at: {self.ec2_ip}:{self.remote_port}/stream")
                
                # Start health monitoring
                self.start_health_monitoring()
                return True
            else:
                print("[-] Failed to start reverse tunnel")
                return False
                
        except Exception as e:
            print(f"[-] Error starting reverse tunnel: {e}")
            return False
    
    def stop_tunnel(self):
        """Stop SSH reverse tunnel"""
        if not self.is_running:
            print("[+] No active reverse tunnel to stop")
            return
        
        try:
            print("[+] Stopping reverse tunnel...")
            self.is_running = False
            
            if self.tunnel_process:
                self.tunnel_process.terminate()
                try:
                    self.tunnel_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.tunnel_process.kill()
                    self.tunnel_process.wait()
                
                self.tunnel_process = None
            
            print("[+] Reverse tunnel stopped")
            
        except Exception as e:
            print(f"[-] Error stopping reverse tunnel: {e}")
    
    def start_health_monitoring(self):
        """Start health monitoring thread"""
        if self.tunnel_thread and self.tunnel_thread.is_alive():
            return
        
        self.tunnel_thread = threading.Thread(target=self._health_monitor, daemon=True)
        self.tunnel_thread.start()
        print("[+] Tunnel health monitoring started")
    
    def _health_monitor(self):
        """Monitor tunnel health and reconnect if needed"""
        while self.is_running:
            try:
                time.sleep(self.health_check_interval)
                
                if not self.is_running:
                    break
                
                # Check if tunnel process is still running
                if self.tunnel_process and self.tunnel_process.poll() is not None:
                    print("[-] Tunnel process died, attempting reconnection...")
                    self._reconnect_tunnel()
                
                # Test tunnel connectivity
                if not self._test_tunnel_connectivity():
                    print("[-] Tunnel connectivity lost, attempting reconnection...")
                    self._reconnect_tunnel()
                
            except Exception as e:
                print(f"[-] Error in health monitor: {e}")
                time.sleep(5)
    
    def _reconnect_tunnel(self):
        """Reconnect the tunnel"""
        try:
            print("[+] Attempting tunnel reconnection...")
            
            # Stop current tunnel
            if self.tunnel_process:
                self.tunnel_process.terminate()
                time.sleep(2)
            
            # Start new tunnel
            if self.start_tunnel():
                print("[+] Tunnel reconnected successfully")
            else:
                print("[-] Failed to reconnect tunnel")
                
        except Exception as e:
            print(f"[-] Error reconnecting tunnel: {e}")
    
    def _test_tunnel_connectivity(self):
        """Test if tunnel is working by checking local port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', self.local_port))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_tunnel_status(self):
        """Get current tunnel status"""
        return {
            "is_running": self.is_running,
            "ec2_ip": self.ec2_ip,
            "local_port": self.local_port,
            "remote_port": self.remote_port,
            "process_alive": self.tunnel_process.poll() is None if self.tunnel_process else False,
            "local_accessible": self._test_tunnel_connectivity()
        }

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print('\n[+] Shutting down reverse tunnel...')
    sys.exit(0)

if __name__ == "__main__":
    # Test the reverse tunnel
    try:
        print("=" * 50)
        print("Reverse Tunnel Test")
        print("=" * 50)
        
        # Configuration
        EC2_IP = "3.27.77.237"
        EC2_USER = "ubuntu"
        LOCAL_PORT = 8080
        REMOTE_PORT = 8001
        
        # Create tunnel manager
        tunnel = ReverseTunnelManager(EC2_IP, EC2_USER, LOCAL_PORT, REMOTE_PORT)
        
        # Start tunnel
        if tunnel.start_tunnel():
            print("\n[+] Reverse tunnel running...")
            print("[+] Press Ctrl+C to stop")
            
            # Set up signal handler
            signal.signal(signal.SIGINT, signal_handler)
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("[-] Failed to start reverse tunnel")
        
    except Exception as e:
        print(f"[-] Error: {e}")
    finally:
        if 'tunnel' in locals():
            tunnel.stop_tunnel()
        print("[+] Cleanup complete")

