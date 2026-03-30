#!/usr/bin/env python3
"""
Render Network Toolkit - Unified Network Functions
Collects all network functions from shell scripts, Python scripts, and commands
into one comprehensive Python script for deployment on Render.
"""

import os
import sys
import subprocess
import socket
import threading
import time
import json
import logging
import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('render_network_toolkit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class NetworkDevice:
    """Represents a network device"""
    ip: str
    mac: str = ""
    hostname: str = ""
    vendor: str = ""
    open_ports: List[int] = None
    last_seen: str = ""
    
    def __post_init__(self):
        if self.open_ports is None:
            self.open_ports = []
        if not self.last_seen:
            self.last_seen = datetime.now().isoformat()


@dataclass
class ConnectionStats:
    """Connection statistics"""
    packets_sent: int = 0
    packets_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    lost_packets: int = 0
    loss_percentage: float = 0.0
    target_size_mb: float = 0.0
    current_size_mb: float = 0.0


class NetworkToolkit:
    """Unified network toolkit combining all network functions"""
    
    def __init__(self, interface: str = None):
        self.interface = interface or self._get_default_interface()
        self.devices: Dict[str, NetworkDevice] = {}
        self.connection_stats = ConnectionStats()
        self.is_monitoring = False
        
    def _get_default_interface(self) -> str:
        """Get default network interface"""
        try:
            result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True, text=True, check=True
            )
            match = re.search(r'dev (\S+)', result.stdout)
            if match:
                return match.group(1)
        except:
            pass
        
        # Fallback to common interfaces
        for iface in ['eth0', 'wlan0', 'enp0s3', 'wlp2s0']:
            try:
                subprocess.run(
                    ['ip', 'link', 'show', iface],
                    capture_output=True, check=True
                )
                return iface
            except:
                continue
        
        return 'eth0'
    
    def get_network_info(self) -> Dict[str, str]:
        """Get network information for the interface"""
        try:
            result = subprocess.run(
                ['ip', 'addr', 'show', self.interface],
                capture_output=True, text=True, check=True
            )
            output = result.stdout
            
            # Parse IP address
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', output)
            if ip_match:
                ip_address = ip_match.group(1)
                cidr = int(ip_match.group(2))
                netmask = self._cidr_to_netmask(cidr)
            else:
                ip_address = "Unknown"
                netmask = "Unknown"
            
            # Parse MAC address
            mac_match = re.search(r'link/ether ([0-9a-fA-F:]+)', output)
            mac_address = mac_match.group(1) if mac_match else "Unknown"
            
            # Get gateway
            gateway = self._get_gateway()
            
            return {
                'interface': self.interface,
                'ip_address': ip_address,
                'netmask': netmask,
                'mac_address': mac_address,
                'gateway': gateway
            }
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return {}
    
    def _cidr_to_netmask(self, cidr: int) -> str:
        """Convert CIDR notation to netmask"""
        mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
        return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"
    
    def _get_gateway(self) -> str:
        """Get default gateway"""
        try:
            result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True, text=True, check=True
            )
            match = re.search(r'via (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
        except:
            pass
        return "Unknown"
    
    def scan_network(self, method: str = 'ping') -> Dict[str, NetworkDevice]:
        """
        Scan network for devices
        
        Methods:
        - arp: Use ARP table (fast, passive)
        - ping: Ping sweep (active, reliable)
        - nmap: Use nmap (comprehensive)
        """
        logger.info(f"Scanning network using {method} method...")
        
        if method == 'arp':
            self._scan_arp()
        elif method == 'ping':
            self._scan_ping()
        elif method == 'nmap':
            self._scan_nmap()
        else:
            logger.error(f"Unknown scan method: {method}")
        
        logger.info(f"Found {len(self.devices)} devices")
        return self.devices
    
    def _scan_arp(self):
        """Scan using ARP table"""
        try:
            result = subprocess.run(
                ['arp', '-a'],
                capture_output=True, text=True, check=True
            )
            
            for line in result.stdout.split('\n'):
                match = re.search(r'(\d+\.\d+\.\d+\.\d+).*?(([0-9a-fA-F]{1,2}:){5}[0-9a-fA-F]{1,2})', line)
                if match:
                    ip = match.group(1)
                    mac = match.group(2).lower()
                    
                    hostname = self._get_hostname(ip)
                    
                    device = NetworkDevice(
                        ip=ip,
                        mac=mac,
                        hostname=hostname
                    )
                    self.devices[ip] = device
                    logger.info(f"Found device: {ip} ({mac}) - {hostname}")
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"Error scanning ARP table: {e}")
    
    def _scan_ping(self):
        """Scan using ping sweep"""
        try:
            result = subprocess.run(
                ['ip', 'addr', 'show', self.interface],
                capture_output=True, text=True, check=True
            )
            output = result.stdout
            
            # Parse network address
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', output)
            if not ip_match:
                logger.error("Could not determine network address")
                return
            
            ip_address = ip_match.group(1)
            cidr = int(ip_match.group(2))
            
            # Calculate network range
            ip_parts = [int(x) for x in ip_address.split('.')]
            host_bits = 32 - cidr
            num_hosts = min(2 ** host_bits - 2, 254)
            
            logger.info(f"Ping sweeping {num_hosts} hosts...")
            
            # Ping sweep
            threads = []
            for i in range(1, num_hosts + 1):
                # Calculate IP
                test_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.{i}"
                
                # Skip self
                if test_ip == ip_address:
                    continue
                
                # Start ping thread
                thread = threading.Thread(target=self._ping_host, args=(test_ip,))
                thread.start()
                threads.append(thread)
                
                # Limit concurrent threads
                if len(threads) >= 50:
                    for t in threads:
                        t.join()
                    threads = []
            
            # Wait for remaining threads
            for thread in threads:
                thread.join()
                
        except Exception as e:
            logger.error(f"Error during ping scan: {e}")
    
    def _ping_host(self, ip: str):
        """Ping a single host"""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', ip],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                mac = self._get_mac_from_arp(ip)
                hostname = self._get_hostname(ip)
                
                device = NetworkDevice(
                    ip=ip,
                    mac=mac,
                    hostname=hostname
                )
                self.devices[ip] = device
                logger.info(f"Found device: {ip} ({mac}) - {hostname}")
                
        except Exception as e:
            logger.debug(f"Error pinging {ip}: {e}")
    
    def _scan_nmap(self):
        """Scan using nmap"""
        try:
            # Check if nmap is installed
            subprocess.run(['nmap', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("nmap is not installed. Install with: sudo apt-get install nmap")
            return
        
        try:
            # Get network address
            result = subprocess.run(
                ['ip', 'addr', 'show', self.interface],
                capture_output=True, text=True, check=True
            )
            output = result.stdout
            
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', output)
            if not ip_match:
                logger.error("Could not determine network address")
                return
            
            ip_address = ip_match.group(1)
            cidr = int(ip_match.group(2))
            netmask = self._cidr_to_netmask(cidr)
            
            logger.info("Running nmap scan...")
            result = subprocess.run(
                ['nmap', '-sn', f'{ip_address}/{cidr}'],
                capture_output=True, text=True, check=True
            )
            
            # Parse nmap output
            current_ip = None
            for line in result.stdout.split('\n'):
                ip_match = re.search(r'Nmap scan report for .*?(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    current_ip = ip_match.group(1)
                    
                    # Skip self
                    if current_ip == ip_address:
                        current_ip = None
                        continue
                    
                    hostname = ""
                    if '(' in line and ')' in line:
                        hostname = line.split('(')[0].strip()
                    
                    device = NetworkDevice(
                        ip=current_ip,
                        hostname=hostname
                    )
                    self.devices[current_ip] = device
                
                mac_match = re.search(r'MAC Address: ([0-9A-Fa-f:]+)', line)
                if mac_match and current_ip:
                    mac = mac_match.group(1).lower()
                    self.devices[current_ip].mac = mac
                    logger.info(f"Found device: {current_ip} ({mac}) - {self.devices[current_ip].hostname}")
                    current_ip = None
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running nmap: {e}")
    
    def _get_mac_from_arp(self, ip: str) -> str:
        """Get MAC address from ARP table"""
        try:
            result = subprocess.run(
                ['arp', '-n', ip],
                capture_output=True, text=True, check=True
            )
            match = re.search(r'(([0-9a-fA-F]{1,2}:){5}[0-9a-fA-F]{1,2})', result.stdout)
            if match:
                return match.group(1).lower()
        except:
            pass
        return ""
    
    def _get_hostname(self, ip: str) -> str:
        """Get hostname for an IP address"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return ""
    
    def scan_ports(self, ip: str, ports: List[int] = None) -> List[int]:
        """Scan common ports on a device"""
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445,
                    993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 8080, 8443]
        
        open_ports = []
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex((ip, port))
                if result == 0:
                    open_ports.append(port)
                sock.close()
            except:
                pass
        
        if open_ports and ip in self.devices:
            self.devices[ip].open_ports = open_ports
            logger.info(f"Device {ip} has open ports: {open_ports}")
        
        return open_ports
    
    def monitor_connection(self, target_ip: str = "8.8.8.8", target_size_mb: int = 3, duration: int = 60):
        """
        Monitor connection stability with automatic recovery
        
        Args:
            target_ip: Target IP to monitor
            target_size_mb: Target size in MB
            duration: Monitoring duration in seconds
        """
        logger.info(f"Starting connection monitoring for {duration} seconds...")
        logger.info(f"Target: {target_ip}, Size: {target_size_mb} MB")
        
        self.is_monitoring = True
        self.connection_stats = ConnectionStats(target_size_mb=target_size_mb)
        
        # Start recovery thread
        recovery_thread = threading.Thread(target=self._recover_connection, args=(target_ip,))
        recovery_thread.daemon = True
        recovery_thread.start()
        
        start_time = time.time()
        target_size_bytes = target_size_mb * 1024 * 1024
        
        try:
            while time.time() - start_time < duration and self.is_monitoring:
                # Send probe packet
                success = self._send_probe_packet(target_ip, size=1024)
                
                # Log status every 10 packets
                if self.connection_stats.packets_sent % 10 == 0:
                    logger.info(
                        f"Progress: {self.connection_stats.current_size_mb:.2f}/{target_size_mb} MB | "
                        f"Sent: {self.connection_stats.packets_sent} | "
                        f"Received: {self.connection_stats.packets_received} | "
                        f"Loss: {self.connection_stats.loss_percentage:.2f}%"
                    )
                
                # Check if we've reached target size
                if self.connection_stats.bytes_sent >= target_size_bytes:
                    logger.info(f"Target size of {target_size_mb} MB reached!")
                    break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
        finally:
            self.is_monitoring = False
        
        # Final statistics
        logger.info("=" * 50)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 50)
        logger.info(f"Total packets sent: {self.connection_stats.packets_sent}")
        logger.info(f"Total packets received: {self.connection_stats.packets_received}")
        logger.info(f"Total bytes sent: {self.connection_stats.bytes_sent}")
        logger.info(f"Total bytes received: {self.connection_stats.bytes_received}")
        logger.info(f"Lost packets: {self.connection_stats.lost_packets}")
        logger.info(f"Loss percentage: {self.connection_stats.loss_percentage:.2f}%")
        logger.info(f"Target size: {target_size_mb} MB")
        logger.info(f"Actual size sent: {self.connection_stats.current_size_mb:.2f} MB")
        logger.info("=" * 50)
        
        return asdict(self.connection_stats)
    
    def _send_probe_packet(self, target_ip: str, size: int = 1024) -> bool:
        """Send a probe packet to check connection"""
        try:
            # Create ICMP packet with payload
            payload = "X" * size
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', target_ip],
                capture_output=True, text=True
            )
            
            self.connection_stats.packets_sent += 1
            self.connection_stats.bytes_sent += size
            
            if result.returncode == 0:
                self.connection_stats.packets_received += 1
                self.connection_stats.bytes_received += size
                return True
            else:
                self.connection_stats.lost_packets += 1
                return False
                
        except Exception as e:
            logger.error(f"Error sending probe packet: {e}")
            self.connection_stats.lost_packets += 1
            return False
    
    def _recover_connection(self, target_ip: str):
        """Background recovery process"""
        logger.info("Starting background recovery process...")
        
        while self.is_monitoring:
            try:
                # Check if we need to recover
                if self.connection_stats.packets_sent > 0:
                    loss_percentage = (self.connection_stats.lost_packets / self.connection_stats.packets_sent) * 100
                    
                    if loss_percentage > 10:  # More than 10% loss
                        logger.warning(f"High packet loss detected: {loss_percentage:.2f}%")
                        logger.info("Attempting connection recovery...")
                        
                        # Send multiple probe packets to stabilize connection
                        for i in range(5):
                            self._send_probe_packet(target_ip, size=512)
                            time.sleep(0.5)
                        
                        # Check if recovery was successful
                        new_loss = (self.connection_stats.lost_packets / self.connection_stats.packets_sent) * 100
                        if new_loss < loss_percentage:
                            logger.info(f"Recovery successful. Loss reduced to {new_loss:.2f}%")
                        else:
                            logger.warning("Recovery attempt failed. Retrying...")
                
                # Wait before next check
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in recovery process: {e}")
                time.sleep(5)
    
    def run_firewall_setup(self, allowed_ports: List[int] = None, denied_ports: List[int] = None):
        """
        Setup firewall with strict rules
        
        Args:
            allowed_ports: List of allowed ports
            denied_ports: List of denied ports
        """
        if allowed_ports is None:
            allowed_ports = [22, 80, 443, 8080, 8443, 3000, 5000, 8000, 9000]
        
        if denied_ports is None:
            denied_ports = [23, 25, 135, 137, 138, 139, 445, 1433, 1434, 3306, 3389, 5432, 5900, 6379]
        
        logger.info("Setting up firewall...")
        
        # Flush existing rules
        subprocess.run(['iptables', '-F'], check=False)
        subprocess.run(['iptables', '-X'], check=False)
        subprocess.run(['iptables', '-t', 'nat', '-F'], check=False)
        subprocess.run(['iptables', '-t', 'nat', '-X'], check=False)
        
        # Set default policies
        subprocess.run(['iptables', '-P', 'INPUT', 'DROP'], check=False)
        subprocess.run(['iptables', '-P', 'FORWARD', 'DROP'], check=False)
        subprocess.run(['iptables', '-P', 'OUTPUT', 'DROP'], check=False)
        
        # Allow loopback
        subprocess.run(['iptables', '-A', 'INPUT', '-i', 'lo', '-j', 'ACCEPT'], check=False)
        subprocess.run(['iptables', '-A', 'OUTPUT', '-o', 'lo', '-j', 'ACCEPT'], check=False)
        
        # Allow established connections
        subprocess.run([
            'iptables', '-A', 'INPUT',
            '-m', 'conntrack',
            '--ctstate', 'ESTABLISHED,RELATED',
            '-j', 'ACCEPT'
        ], check=False)
        subprocess.run([
            'iptables', '-A', 'OUTPUT',
            '-m', 'conntrack',
            '--ctstate', 'ESTABLISHED,RELATED',
            '-j', 'ACCEPT'
        ], check=False)
        
        # Allow specific ports
        for port in allowed_ports:
            logger.info(f"Allowing port {port}...")
            subprocess.run([
                'iptables', '-A', 'INPUT',
                '-p', 'tcp',
                '--dport', str(port),
                '-j', 'ACCEPT'
            ], check=False)
            subprocess.run([
                'iptables', '-A', 'OUTPUT',
                '-p', 'tcp',
                '--sport', str(port),
                '-j', 'ACCEPT'
            ], check=False)
        
        # Deny specific ports
        for port in denied_ports:
            logger.info(f"Denying port {port}...")
            subprocess.run([
                'iptables', '-A', 'INPUT',
                '-p', 'tcp',
                '--dport', str(port),
                '-j', 'DROP'
            ], check=False)
            subprocess.run([
                'iptables', '-A', 'OUTPUT',
                '-p', 'tcp',
                '--sport', str(port),
                '-j', 'DROP'
            ], check=False)
        
        # Rate limiting for SSH
        subprocess.run([
            'iptables', '-A', 'INPUT',
            '-p', 'tcp',
            '--dport', '22',
            '-m', 'limit',
            '--limit', '3/min',
            '--limit-burst', '3',
            '-j', 'ACCEPT'
        ], check=False)
        
        # SYN flood protection
        subprocess.run([
            'iptables', '-A', 'INPUT',
            '-p', 'tcp',
            '--syn',
            '-m', 'limit',
            '--limit', '1/s',
            '--limit-burst', '3',
            '-j', 'ACCEPT'
        ], check=False)
        
        # ICMP rate limiting
        subprocess.run([
            'iptables', '-A', 'INPUT',
            '-p', 'icmp',
            '--icmp-type', 'echo-request',
            '-m', 'limit',
            '--limit', '1/s',
            '--limit-burst', '4',
            '-j', 'ACCEPT'
        ], check=False)
        
        logger.info("Firewall setup complete")
    
    def save_devices(self, filename: str = 'network_devices.json'):
        """Save discovered devices to JSON file"""
        data = {
            'scan_time': datetime.now().isoformat(),
            'interface': self.interface,
            'devices': [asdict(device) for device in self.devices.values()]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved {len(self.devices)} devices to {filename}")
    
    def load_devices(self, filename: str = 'network_devices.json') -> bool:
        """Load devices from JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.devices = {}
            for device_data in data.get('devices', []):
                device = NetworkDevice(**device_data)
                self.devices[device.ip] = device
            
            logger.info(f"Loaded {len(self.devices)} devices from {filename}")
            return True
        except FileNotFoundError:
            logger.warning(f"File {filename} not found")
            return False
        except Exception as e:
            logger.error(f"Error loading devices: {e}")
            return False


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Render Network Toolkit - Unified Network Functions')
    parser.add_argument('--interface', help='Network interface to use')
    parser.add_argument('--scan', choices=['arp', 'ping', 'nmap'], help='Scan network for devices')
    parser.add_argument('--scan-ports', help='Scan ports on specific IP')
    parser.add_argument('--monitor', help='Monitor connection to target IP')
    parser.add_argument('--monitor-size', type=int, default=3, help='Target size in MB for monitoring')
    parser.add_argument('--monitor-duration', type=int, default=60, help='Monitoring duration in seconds')
    parser.add_argument('--firewall', action='store_true', help='Setup firewall rules')
    parser.add_argument('--info', action='store_true', help='Show network information')
    parser.add_argument('--save', help='Save devices to JSON file')
    parser.add_argument('--load', help='Load devices from JSON file')
    
    args = parser.parse_args()
    
    # Create toolkit instance
    toolkit = NetworkToolkit(interface=args.interface)
    
    # Show network information
    if args.info:
        info = toolkit.get_network_info()
        print("\nNetwork Information:")
        print("=" * 50)
        for key, value in info.items():
            print(f"{key}: {value}")
        print("=" * 50)
        return
    
    # Scan network
    if args.scan:
        devices = toolkit.scan_network(method=args.scan)
        print(f"\nFound {len(devices)} devices:")
        print("=" * 50)
        for ip, device in devices.items():
            print(f"IP: {ip}")
            print(f"  MAC: {device.mac}")
            print(f"  Hostname: {device.hostname}")
            if device.open_ports:
                print(f"  Open Ports: {device.open_ports}")
            print()
        
        if args.save:
            toolkit.save_devices(args.save)
        return
    
    # Scan ports
    if args.scan_ports:
        open_ports = toolkit.scan_ports(args.scan_ports)
        print(f"\nOpen ports on {args.scan_ports}: {open_ports}")
        return
    
    # Monitor connection
    if args.monitor:
        stats = toolkit.monitor_connection(
            target_ip=args.monitor,
            target_size_mb=args.monitor_size,
            duration=args.monitor_duration
        )
        print("\nConnection Statistics:")
        print("=" * 50)
        for key, value in stats.items():
            print(f"{key}: {value}")
        return
    
    # Setup firewall
    if args.firewall:
        toolkit.run_firewall_setup()
        return
    
    # Load devices
    if args.load:
        toolkit.load_devices(args.load)
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
