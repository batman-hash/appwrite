#!/usr/bin/env python3
"""
Connection Stability Script using Scapy
Monitors network connection, detects packet loss, and recovers in background
Target: 3 MB connection with automatic recovery
Includes firewall functionality to disable all remote ports
"""

import time
import threading
import logging
import subprocess
import platform
import sys
import os
from datetime import datetime

# Check for root privileges before importing scapy (Unix-like systems only)
try:
    if hasattr(os, 'geteuid') and os.geteuid() != 0:
        print("WARNING: This script works best with root privileges for raw packet operations.")
        print("If you encounter permission errors, run with sudo:")
        print(f"  sudo {sys.executable} {' '.join(sys.argv)}")
        print("Continuing anyway - will use system ping fallback if needed...\n")
except Exception:
    pass

try:
    from scapy.all import *
    from scapy.layers.inet import IP, TCP, ICMP
    SCAPY_AVAILABLE = True
except ImportError:
    logging.error("Scapy is not installed. Install it with: pip install scapy")
    SCAPY_AVAILABLE = False
except Exception as e:
    logging.warning(f"Could not import Scapy: {e}. Will use system ping fallback.")
    SCAPY_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('connection_stability.log'),
        logging.StreamHandler()
    ]
)

class FirewallManager:
    """Manages firewall rules to disable all remote ports"""
    
    def __init__(self):
        self.os_type = platform.system().lower()
        self.blocked_ports = []
        self.is_blocking = False
        self.lock = threading.Lock()
        
    def disable_all_remote_ports(self):
        """Disable all remote ports using system firewall"""
        with self.lock:
            if self.is_blocking:
                logging.warning("Firewall is already blocking ports")
                return True
                
            try:
                logging.info("Disabling all remote ports via firewall...")
                
                if self.os_type == "linux":
                    return self._disable_ports_linux()
                elif self.os_type == "windows":
                    return self._disable_ports_windows()
                elif self.os_type == "darwin":
                    return self._disable_ports_macos()
                else:
                    logging.error(f"Unsupported operating system: {self.os_type}")
                    return False
                    
            except Exception as e:
                logging.error(f"Error disabling remote ports: {e}")
                return False
    
    def _disable_ports_linux(self):
        """Disable ports using iptables on Linux"""
        try:
            # Flush existing rules
            subprocess.run(["sudo", "iptables", "-F"], check=True, capture_output=True)
            subprocess.run(["sudo", "iptables", "-X"], check=True, capture_output=True)
            
            # Set default policies to DROP for incoming and forwarded traffic
            subprocess.run(["sudo", "iptables", "-P", "INPUT", "DROP"], check=True, capture_output=True)
            subprocess.run(["sudo", "iptables", "-P", "FORWARD", "DROP"], check=True, capture_output=True)
            
            # Allow loopback interface
            subprocess.run(["sudo", "iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["sudo", "iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"], check=True, capture_output=True)
            
            # Allow established and related connections
            subprocess.run(["sudo", "iptables", "-A", "INPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"], check=True, capture_output=True)
            
            # Allow outgoing traffic
            subprocess.run(["sudo", "iptables", "-P", "OUTPUT", "ACCEPT"], check=True, capture_output=True)
            
            # Block all incoming TCP ports
            for port in range(1, 65536):
                subprocess.run(["sudo", "iptables", "-A", "INPUT", "-p", "tcp", "--dport", str(port), "-j", "DROP"], check=False, capture_output=True)
                self.blocked_ports.append(port)
            
            # Block all incoming UDP ports
            for port in range(1, 65536):
                subprocess.run(["sudo", "iptables", "-A", "INPUT", "-p", "udp", "--dport", str(port), "-j", "DROP"], check=False, capture_output=True)
            
            self.is_blocking = True
            logging.info(f"Successfully blocked all remote ports on Linux (blocked {len(self.blocked_ports)} ports)")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"iptables command failed: {e}")
            return False
        except Exception as e:
            logging.error(f"Error in Linux firewall configuration: {e}")
            return False
    
    def _disable_ports_windows(self):
        """Disable ports using netsh on Windows"""
        try:
            # Create firewall rule to block all inbound connections
            cmd = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                "name=Block All Inbound",
                "dir=in",
                "action=block",
                "protocol=TCP",
                "localport=1-65535",
                "enable=yes"
            ]
            subprocess.run(cmd, check=True, capture_output=True, shell=True)
            
            # Block UDP ports
            cmd_udp = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                "name=Block All Inbound UDP",
                "dir=in",
                "action=block",
                "protocol=UDP",
                "localport=1-65535",
                "enable=yes"
            ]
            subprocess.run(cmd_udp, check=True, capture_output=True, shell=True)
            
            self.is_blocking = True
            logging.info("Successfully blocked all remote ports on Windows")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"netsh command failed: {e}")
            return False
        except Exception as e:
            logging.error(f"Error in Windows firewall configuration: {e}")
            return False
    
    def _disable_ports_macos(self):
        """Disable ports using pfctl on macOS"""
        try:
            # Create pfctl rules to block all incoming connections
            pf_rules = """
block in all
block in proto tcp from any to any
block in proto udp from any to any
pass out all
pass in on lo0
"""
            # Write rules to temporary file
            with open("/tmp/pf_rules.conf", "w") as f:
                f.write(pf_rules)
            
            # Load and enable pfctl rules
            subprocess.run(["sudo", "pfctl", "-f", "/tmp/pf_rules.conf"], check=True, capture_output=True)
            subprocess.run(["sudo", "pfctl", "-e"], check=True, capture_output=True)
            
            self.is_blocking = True
            logging.info("Successfully blocked all remote ports on macOS")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"pfctl command failed: {e}")
            return False
        except Exception as e:
            logging.error(f"Error in macOS firewall configuration: {e}")
            return False
    
    def enable_all_remote_ports(self):
        """Re-enable all remote ports by removing firewall rules"""
        with self.lock:
            if not self.is_blocking:
                logging.warning("Firewall is not currently blocking ports")
                return True
                
            try:
                logging.info("Re-enabling all remote ports...")
                
                if self.os_type == "linux":
                    return self._enable_ports_linux()
                elif self.os_type == "windows":
                    return self._enable_ports_windows()
                elif self.os_type == "darwin":
                    return self._enable_ports_macos()
                else:
                    logging.error(f"Unsupported operating system: {self.os_type}")
                    return False
                    
            except Exception as e:
                logging.error(f"Error enabling remote ports: {e}")
                return False
    
    def _enable_ports_linux(self):
        """Re-enable ports by resetting iptables on Linux"""
        try:
            # Flush all rules
            subprocess.run(["sudo", "iptables", "-F"], check=True, capture_output=True)
            subprocess.run(["sudo", "iptables", "-X"], check=True, capture_output=True)
            
            # Set default policies to ACCEPT
            subprocess.run(["sudo", "iptables", "-P", "INPUT", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["sudo", "iptables", "-P", "FORWARD", "ACCEPT"], check=True, capture_output=True)
            subprocess.run(["sudo", "iptables", "-P", "OUTPUT", "ACCEPT"], check=True, capture_output=True)
            
            self.blocked_ports.clear()
            self.is_blocking = False
            logging.info("Successfully re-enabled all remote ports on Linux")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"iptables command failed: {e}")
            return False
        except Exception as e:
            logging.error(f"Error in Linux firewall configuration: {e}")
            return False
    
    def _enable_ports_windows(self):
        """Re-enable ports by removing Windows firewall rules"""
        try:
            # Remove the blocking rules
            cmd = [
                "netsh", "advfirewall", "firewall", "delete", "rule",
                "name=Block All Inbound"
            ]
            subprocess.run(cmd, check=False, capture_output=True, shell=True)
            
            cmd_udp = [
                "netsh", "advfirewall", "firewall", "delete", "rule",
                "name=Block All Inbound UDP"
            ]
            subprocess.run(cmd_udp, check=False, capture_output=True, shell=True)
            
            self.is_blocking = False
            logging.info("Successfully re-enabled all remote ports on Windows")
            return True
            
        except Exception as e:
            logging.error(f"Error in Windows firewall configuration: {e}")
            return False
    
    def _enable_ports_macos(self):
        """Re-enable ports by disabling pfctl on macOS"""
        try:
            # Disable pfctl
            subprocess.run(["sudo", "pfctl", "-d"], check=True, capture_output=True)
            
            # Remove temporary rules file
            subprocess.run(["rm", "-f", "/tmp/pf_rules.conf"], check=False, capture_output=True)
            
            self.is_blocking = False
            logging.info("Successfully re-enabled all remote ports on macOS")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"pfctl command failed: {e}")
            return False
        except Exception as e:
            logging.error(f"Error in macOS firewall configuration: {e}")
            return False
    
    def get_firewall_status(self):
        """Get current firewall status"""
        with self.lock:
            return {
                'is_blocking': self.is_blocking,
                'blocked_ports_count': len(self.blocked_ports),
                'os_type': self.os_type
            }

class ConnectionStability:
    def __init__(self, target_ip="8.8.8.8", target_size_mb=3, enable_firewall=False):
        self.target_ip = target_ip
        self.target_size_mb = target_size_mb
        self.target_size_bytes = target_size_mb * 1024 * 1024
        self.packets_sent = 0
        self.packets_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.lost_packets = 0
        self.is_running = False
        self.recovery_thread = None
        self.lock = threading.Lock()
        self.enable_firewall = enable_firewall
        self.firewall = FirewallManager() if enable_firewall else None
        
    def send_probe_packet(self, size=1024):
        """Send a probe packet to check connection"""
        # If Scapy is not available, use fallback immediately
        if not SCAPY_AVAILABLE:
            return self._send_probe_ping_fallback(size)
            
        try:
            # Create ICMP packet with payload
            payload = Raw(load="X" * size)
            packet = IP(dst=self.target_ip) / ICMP() / payload
            
            # Send packet and wait for response
            reply = sr1(packet, timeout=2, verbose=0)
            
            with self.lock:
                self.packets_sent += 1
                self.bytes_sent += size
                
                if reply:
                    self.packets_received += 1
                    self.bytes_received += len(reply)
                    return True
                else:
                    self.lost_packets += 1
                    return False
                    
        except PermissionError as e:
            logging.warning(f"Scapy permission denied, falling back to system ping: {e}")
            # Fallback to system ping command
            return self._send_probe_ping_fallback(size)
        except Exception as e:
            logging.warning(f"Scapy failed, falling back to system ping: {e}")
            # Fallback to system ping command
            return self._send_probe_ping_fallback(size)
    
    def _send_probe_ping_fallback(self, size=1024):
        """Fallback method using system ping command"""
        try:
            # Use system ping command as fallback
            # -c 1: send only 1 packet
            # -W 2: timeout after 2 seconds
            # -s size: packet size
            cmd = ["ping", "-c", "1", "-W", "2", "-s", str(size), self.target_ip]
            result = subprocess.run(cmd, capture_output=True, timeout=3)
            
            with self.lock:
                self.packets_sent += 1
                self.bytes_sent += size
                
                if result.returncode == 0:
                    self.packets_received += 1
                    self.bytes_received += size  # Approximate
                    return True
                else:
                    self.lost_packets += 1
                    return False
                    
        except Exception as e:
            logging.error(f"Fallback ping also failed: {e}")
            with self.lock:
                self.lost_packets += 1
            return False
    
    def calculate_loss_percentage(self):
        """Calculate packet loss percentage"""
        with self.lock:
            if self.packets_sent == 0:
                return 0.0
            return (self.lost_packets / self.packets_sent) * 100
    
    def get_connection_stats(self):
        """Get current connection statistics"""
        with self.lock:
            stats = {
                'packets_sent': self.packets_sent,
                'packets_received': self.packets_received,
                'bytes_sent': self.bytes_sent,
                'bytes_received': self.bytes_received,
                'lost_packets': self.lost_packets,
                'loss_percentage': self.calculate_loss_percentage(),
                'target_size_mb': self.target_size_mb,
                'current_size_mb': self.bytes_sent / (1024 * 1024)
            }
            
            # Add firewall status if enabled
            if self.firewall:
                stats['firewall_status'] = self.firewall.get_firewall_status()
            
            return stats
    
    def recover_connection(self):
        """Background recovery process"""
        logging.info("Starting background recovery process...")
        
        while self.is_running:
            try:
                # Check if we need to recover
                loss_percentage = self.calculate_loss_percentage()
                
                if loss_percentage > 10:  # More than 10% loss
                    logging.warning(f"High packet loss detected: {loss_percentage:.2f}%")
                    logging.info("Attempting connection recovery...")
                    
                    # Send multiple probe packets to stabilize connection
                    for i in range(5):
                        self.send_probe_packet(size=512)
                        time.sleep(0.5)
                    
                    # Check if recovery was successful
                    new_loss = self.calculate_loss_percentage()
                    if new_loss < loss_percentage:
                        logging.info(f"Recovery successful. Loss reduced to {new_loss:.2f}%")
                    else:
                        logging.warning("Recovery attempt failed. Retrying...")
                
                # Wait before next check
                time.sleep(5)
                
            except Exception as e:
                logging.error(f"Error in recovery process: {e}")
                time.sleep(5)
    
    def monitor_connection(self, duration=60, interval=1):
        """Monitor connection for specified duration"""
        logging.info(f"Starting connection monitoring for {duration} seconds...")
        logging.info(f"Target: {self.target_ip}, Size: {self.target_size_mb} MB")
        
        # Enable firewall if configured
        if self.firewall:
            logging.info("Enabling firewall to block all remote ports...")
            if self.firewall.disable_all_remote_ports():
                logging.info("Firewall successfully enabled - all remote ports blocked")
            else:
                logging.error("Failed to enable firewall")
        
        self.is_running = True
        
        # Start recovery thread
        self.recovery_thread = threading.Thread(target=self.recover_connection, daemon=True)
        self.recovery_thread.start()
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration and self.is_running:
                # Send probe packet
                success = self.send_probe_packet(size=1024)
                
                # Log status every 10 packets
                if self.packets_sent % 10 == 0:
                    stats = self.get_connection_stats()
                    logging.info(
                        f"Progress: {stats['current_size_mb']:.2f}/{stats['target_size_mb']} MB | "
                        f"Sent: {stats['packets_sent']} | "
                        f"Received: {stats['packets_received']} | "
                        f"Loss: {stats['loss_percentage']:.2f}%"
                    )
                    
                    # Log firewall status if enabled
                    if self.firewall and 'firewall_status' in stats:
                        fw_status = stats['firewall_status']
                        logging.info(f"Firewall: Blocking {fw_status['blocked_ports_count']} ports")
                
                # Check if we've reached target size
                if self.bytes_sent >= self.target_size_bytes:
                    logging.info(f"Target size of {self.target_size_mb} MB reached!")
                    break
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logging.info("Monitoring interrupted by user")
        finally:
            self.is_running = False
            if self.recovery_thread:
                self.recovery_thread.join(timeout=5)
            
            # Disable firewall if it was enabled
            if self.firewall and self.firewall.is_blocking:
                logging.info("Disabling firewall and re-enabling all remote ports...")
                if self.firewall.enable_all_remote_ports():
                    logging.info("Firewall disabled - all remote ports re-enabled")
                else:
                    logging.error("Failed to disable firewall")
        
        # Final statistics
        stats = self.get_connection_stats()
        logging.info("=" * 50)
        logging.info("FINAL STATISTICS")
        logging.info("=" * 50)
        logging.info(f"Total packets sent: {stats['packets_sent']}")
        logging.info(f"Total packets received: {stats['packets_received']}")
        logging.info(f"Total bytes sent: {stats['bytes_sent']}")
        logging.info(f"Total bytes received: {stats['bytes_received']}")
        logging.info(f"Lost packets: {stats['lost_packets']}")
        logging.info(f"Loss percentage: {stats['loss_percentage']:.2f}%")
        logging.info(f"Target size: {stats['target_size_mb']} MB")
        logging.info(f"Actual size sent: {stats['current_size_mb']:.2f} MB")
        
        if self.firewall:
            logging.info(f"Firewall was enabled: {self.firewall.is_blocking}")
            logging.info(f"Ports blocked: {self.firewall.get_firewall_status()['blocked_ports_count']}")
        
        logging.info("=" * 50)
        
        return stats

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Connection Stability Monitor using Scapy with Firewall')
    parser.add_argument('--target', default='8.8.8.8', help='Target IP address (default: 8.8.8.8)')
    parser.add_argument('--size', type=int, default=3, help='Target size in MB (default: 3)')
    parser.add_argument('--duration', type=int, default=60, help='Monitoring duration in seconds (default: 60)')
    parser.add_argument('--interval', type=float, default=1, help='Packet send interval in seconds (default: 1)')
    parser.add_argument('--firewall', action='store_true', help='Enable firewall to block all remote ports')
    parser.add_argument('--disable-firewall-only', action='store_true', help='Only disable firewall without monitoring')
    parser.add_argument('--enable-firewall-only', action='store_true', help='Only enable firewall (re-enable ports) without monitoring')
    
    args = parser.parse_args()
    
    # Handle firewall-only operations
    if args.disable_firewall_only:
        logging.info("Disabling firewall only...")
        firewall = FirewallManager()
        if firewall.disable_all_remote_ports():
            logging.info("Firewall disabled successfully - all remote ports blocked")
            return 0
        else:
            logging.error("Failed to disable firewall")
            return 1
    
    if args.enable_firewall_only:
        logging.info("Enabling firewall only (re-enabling ports)...")
        firewall = FirewallManager()
        if firewall.enable_all_remote_ports():
            logging.info("Firewall enabled successfully - all remote ports re-enabled")
            return 0
        else:
            logging.error("Failed to enable firewall")
            return 1
    
    # Create connection stability monitor
    monitor = ConnectionStability(
        target_ip=args.target,
        target_size_mb=args.size,
        enable_firewall=args.firewall
    )
    
    # Start monitoring
    stats = monitor.monitor_connection(
        duration=args.duration,
        interval=args.interval
    )
    
    # Exit with error code if high packet loss
    if stats['loss_percentage'] > 20:
        logging.error("High packet loss detected. Exiting with error code.")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
