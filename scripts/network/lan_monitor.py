#!/usr/bin/env python3
"""
LAN Device Discovery and Monitoring Script

This script:
1. Discovers all devices on the local network
2. Identifies which IPs are not your device
3. Monitors suspicious activity using ncat
4. Logs all findings

Usage:
    python3 lan_monitor.py --interface eth0 --monitor-duration 300
    python3 lan_monitor.py --scan-only
    python3 lan_monitor.py --monitor-only --suspicious-ips 192.168.1.100,192.168.1.101
"""

import argparse
import json
import logging
import os
import platform
import re
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
import threading
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lan_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class Device:
    """Represents a device on the network"""
    ip: str
    mac: str = ""
    hostname: str = ""
    vendor: str = ""
    is_self: bool = False
    open_ports: List[int] = None
    last_seen: str = ""
    suspicious_activity: List[str] = None
    
    def __post_init__(self):
        if self.open_ports is None:
            self.open_ports = []
        if self.suspicious_activity is None:
            self.suspicious_activity = []
        if not self.last_seen:
            self.last_seen = datetime.now().isoformat()


@dataclass
class NetworkInfo:
    """Network information"""
    interface: str
    ip_address: str
    netmask: str
    network: str
    broadcast: str
    gateway: str
    mac_address: str


class LANDiscovery:
    """Discovers devices on the local network"""
    
    def __init__(self, interface: str = None):
        self.interface = interface
        self.network_info = self._get_network_info()
        self.devices: Dict[str, Device] = {}
        self.self_ip = self.network_info.ip_address if self.network_info else None
        
    def _get_network_info(self) -> Optional[NetworkInfo]:
        """Get network information for the specified interface"""
        try:
            # Get default interface if not specified
            if not self.interface:
                self.interface = self._get_default_interface()
            
            # Get IP address and netmask
            if platform.system() == "Linux":
                result = subprocess.run(
                    ['ip', 'addr', 'show', self.interface],
                    capture_output=True, text=True, check=True
                )
                output = result.stdout
                
                # Parse IP address
                ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', output)
                if ip_match:
                    ip_address = ip_match.group(1)
                    netmask = self._cidr_to_netmask(int(ip_match.group(2)))
                else:
                    logger.error(f"Could not find IP address for interface {self.interface}")
                    return None
                
                # Parse MAC address
                mac_match = re.search(r'link/ether ([0-9a-fA-F:]+)', output)
                mac_address = mac_match.group(1) if mac_match else ""
                
                # Get gateway
                gateway = self._get_gateway()
                
                # Calculate network address
                network = self._calculate_network(ip_address, netmask)
                broadcast = self._calculate_broadcast(ip_address, netmask)
                
                return NetworkInfo(
                    interface=self.interface,
                    ip_address=ip_address,
                    netmask=netmask,
                    network=network,
                    broadcast=broadcast,
                    gateway=gateway,
                    mac_address=mac_address
                )
            else:
                logger.error(f"Unsupported platform: {platform.system()}")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting network info: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def _get_default_interface(self) -> str:
        """Get the default network interface"""
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
        
        # Fallback: try common interfaces
        for iface in ['eth0', 'wlan0', 'enp0s3', 'wlp2s0']:
            try:
                subprocess.run(
                    ['ip', 'link', 'show', iface],
                    capture_output=True, check=True
                )
                return iface
            except:
                continue
        
        raise RuntimeError("Could not determine default network interface")
    
    def _cidr_to_netmask(self, cidr: int) -> str:
        """Convert CIDR notation to netmask"""
        mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
        return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"
    
    def _calculate_network(self, ip: str, netmask: str) -> str:
        """Calculate network address"""
        ip_parts = [int(x) for x in ip.split('.')]
        mask_parts = [int(x) for x in netmask.split('.')]
        network_parts = [ip_parts[i] & mask_parts[i] for i in range(4)]
        return '.'.join(str(x) for x in network_parts)
    
    def _calculate_broadcast(self, ip: str, netmask: str) -> str:
        """Calculate broadcast address"""
        ip_parts = [int(x) for x in ip.split('.')]
        mask_parts = [int(x) for x in netmask.split('.')]
        broadcast_parts = [ip_parts[i] | (255 - mask_parts[i]) for i in range(4)]
        return '.'.join(str(x) for x in broadcast_parts)
    
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
        return ""
    
    def scan_network(self, method: str = 'arp') -> Dict[str, Device]:
        """
        Scan the network for devices
        
        Methods:
        - arp: Use ARP table (fast, passive)
        - ping: Ping sweep (active, reliable)
        - nmap: Use nmap (comprehensive)
        """
        logger.info(f"Scanning network {self.network_info.network}/{self.network_info.netmask}")
        logger.info(f"Self IP: {self.self_ip}")
        
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
                # Parse ARP entries
                match = re.search(r'(\d+\.\d+\.\d+\.\d+).*?(([0-9a-fA-F]{1,2}:){5}[0-9a-fA-F]{1,2})', line)
                if match:
                    ip = match.group(1)
                    mac = match.group(2).lower()
                    
                    # Skip self
                    if ip == self.self_ip:
                        continue
                    
                    # Get hostname
                    hostname = self._get_hostname(ip)
                    
                    device = Device(
                        ip=ip,
                        mac=mac,
                        hostname=hostname,
                        is_self=False
                    )
                    self.devices[ip] = device
                    logger.info(f"Found device: {ip} ({mac}) - {hostname}")
                    
        except subprocess.CalledProcessError as e:
            logger.error(f"Error scanning ARP table: {e}")
    
    def _scan_ping(self):
        """Scan using ping sweep"""
        if not self.network_info:
            logger.error("No network info available")
            return
        
        # Parse network address
        network_parts = [int(x) for x in self.network_info.network.split('.')]
        netmask_parts = [int(x) for x in self.network_info.netmask.split('.')]
        
        # Calculate number of hosts
        host_bits = 32 - bin(int(''.join(format(x, '08b') for x in netmask_parts), 2)).count('1')
        num_hosts = min(2 ** host_bits - 2, 254)  # Limit to 254 hosts
        
        logger.info(f"Ping sweeping {num_hosts} hosts...")
        
        # Ping sweep
        threads = []
        for i in range(1, num_hosts + 1):
            # Calculate IP
            ip_parts = network_parts.copy()
            ip_parts[3] = i
            ip = '.'.join(str(x) for x in ip_parts)
            
            # Skip self and network/broadcast
            if ip == self.self_ip or ip == self.network_info.network or ip == self.network_info.broadcast:
                continue
            
            # Start ping thread
            thread = threading.Thread(target=self._ping_host, args=(ip,))
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
    
    def _ping_host(self, ip: str):
        """Ping a single host"""
        try:
            # Ping with 1 packet, 1 second timeout
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', ip],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                # Host is up
                mac = self._get_mac_from_arp(ip)
                hostname = self._get_hostname(ip)
                
                device = Device(
                    ip=ip,
                    mac=mac,
                    hostname=hostname,
                    is_self=False
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
            logger.info("Running nmap scan...")
            result = subprocess.run(
                ['nmap', '-sn', self.network_info.network + '/' + self.network_info.netmask],
                capture_output=True, text=True, check=True
            )
            
            # Parse nmap output
            current_ip = None
            for line in result.stdout.split('\n'):
                # Look for IP addresses
                ip_match = re.search(r'Nmap scan report for .*?(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    current_ip = ip_match.group(1)
                    
                    # Skip self
                    if current_ip == self.self_ip:
                        current_ip = None
                        continue
                    
                    # Get hostname
                    hostname = ""
                    if '(' in line and ')' in line:
                        hostname = line.split('(')[0].strip()
                    
                    device = Device(
                        ip=current_ip,
                        hostname=hostname,
                        is_self=False
                    )
                    self.devices[current_ip] = device
                
                # Look for MAC addresses
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
            # Common ports
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
    
    def save_devices(self, filename: str = 'lan_devices.json'):
        """Save discovered devices to JSON file"""
        data = {
            'scan_time': datetime.now().isoformat(),
            'network_info': asdict(self.network_info) if self.network_info else None,
            'self_ip': self.self_ip,
            'devices': [asdict(device) for device in self.devices.values()]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved {len(self.devices)} devices to {filename}")
    
    def load_devices(self, filename: str = 'lan_devices.json') -> bool:
        """Load devices from JSON file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.devices = {}
            for device_data in data.get('devices', []):
                device = Device(**device_data)
                self.devices[device.ip] = device
            
            logger.info(f"Loaded {len(self.devices)} devices from {filename}")
            return True
        except FileNotFoundError:
            logger.warning(f"File {filename} not found")
            return False
        except Exception as e:
            logger.error(f"Error loading devices: {e}")
            return False


class NcatMonitor:
    """Monitors suspicious IPs using ncat"""
    
    def __init__(self, suspicious_ips: List[str], ports: List[int] = None):
        self.suspicious_ips = suspicious_ips
        self.ports = ports or [80, 443, 8080, 8443, 22, 23, 21, 3389]
        self.monitoring = False
        self.processes: Dict[str, subprocess.Popen] = {}
        self.log_file = 'ncat_monitor.log'
        
    def start_monitoring(self, duration: int = 0):
        """Start monitoring suspicious IPs"""
        self.monitoring = True
        logger.info(f"Starting ncat monitoring for {len(self.suspicious_ips)} IPs")
        logger.info(f"Monitoring ports: {self.ports}")
        
        # Start monitoring threads
        threads = []
        for ip in self.suspicious_ips:
            thread = threading.Thread(target=self._monitor_ip, args=(ip,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Monitor for specified duration
        if duration > 0:
            logger.info(f"Monitoring for {duration} seconds...")
            time.sleep(duration)
            self.stop_monitoring()
        else:
            logger.info("Monitoring indefinitely (press Ctrl+C to stop)...")
            try:
                while self.monitoring:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop_monitoring()
    
    def _monitor_ip(self, ip: str):
        """Monitor a single IP using ncat"""
        for port in self.ports:
            if not self.monitoring:
                break
            
            try:
                # Use ncat to listen for connections from this IP
                cmd = ['ncat', '-l', '-p', str(port), '--allow', ip, '-v']
                
                logger.info(f"Starting ncat listener for {ip}:{port}")
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                self.processes[f"{ip}:{port}"] = process
                
                # Monitor output
                while self.monitoring:
                    output = process.stderr.readline()
                    if output:
                        timestamp = datetime.now().isoformat()
                        log_entry = f"[{timestamp}] {ip}:{port} - {output.strip()}"
                        logger.warning(log_entry)
                        
                        # Log to file
                        with open(self.log_file, 'a') as f:
                            f.write(log_entry + '\n')
                    
                    # Check if process is still running
                    if process.poll() is not None:
                        break
                
            except Exception as e:
                logger.error(f"Error monitoring {ip}:{port}: {e}")
    
    def stop_monitoring(self):
        """Stop all monitoring processes"""
        self.monitoring = False
        logger.info("Stopping ncat monitoring...")
        
        for key, process in self.processes.items():
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"Stopped monitoring {key}")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.warning(f"Force killed monitoring {key}")
            except Exception as e:
                logger.error(f"Error stopping {key}: {e}")
        
        self.processes.clear()


class ConnectionMonitor:
    """Monitors active connections to detect suspicious activity"""
    
    def __init__(self, self_ip: str):
        self.self_ip = self_ip
        self.suspicious_ips: Set[str] = set()
        self.connection_log = 'connection_monitor.log'
        
    def monitor_connections(self, duration: int = 0):
        """Monitor active connections"""
        logger.info("Starting connection monitoring...")
        
        start_time = time.time()
        while True:
            try:
                # Get active connections
                connections = self._get_active_connections()
                
                # Check for suspicious activity
                for conn in connections:
                    if self._is_suspicious(conn):
                        self.suspicious_ips.add(conn['remote_ip'])
                        self._log_suspicious(conn)
                
                # Check duration
                if duration > 0 and (time.time() - start_time) > duration:
                    break
                
                time.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error monitoring connections: {e}")
                time.sleep(5)
        
        logger.info(f"Found {len(self.suspicious_ips)} suspicious IPs")
        return list(self.suspicious_ips)
    
    def _get_active_connections(self) -> List[Dict]:
        """Get list of active connections"""
        connections = []
        
        try:
            # Use netstat to get connections
            result = subprocess.run(
                ['netstat', '-tunap'],
                capture_output=True, text=True, check=True
            )
            
            for line in result.stdout.split('\n'):
                # Parse TCP connections
                if 'tcp' in line.lower() and 'established' in line.lower():
                    parts = line.split()
                    if len(parts) >= 5:
                        local_addr = parts[3]
                        remote_addr = parts[4]
                        
                        # Parse addresses
                        local_ip, local_port = self._parse_address(local_addr)
                        remote_ip, remote_port = self._parse_address(remote_addr)
                        
                        if remote_ip and remote_ip != self.self_ip:
                            connections.append({
                                'local_ip': local_ip,
                                'local_port': local_port,
                                'remote_ip': remote_ip,
                                'remote_port': remote_port,
                                'state': parts[5] if len(parts) > 5 else ''
                            })
                            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting connections: {e}")
        
        return connections
    
    def _parse_address(self, addr: str) -> tuple:
        """Parse IP:PORT address"""
        if ':' in addr:
            parts = addr.rsplit(':', 1)
            return parts[0], int(parts[1])
        return addr, 0
    
    def _is_suspicious(self, connection: Dict) -> bool:
        """Check if a connection is suspicious"""
        remote_port = connection['remote_port']
        
        # Suspicious ports
        suspicious_ports = [22, 23, 3389, 5900, 8080, 8443]
        
        # Check for connections to sensitive ports
        if remote_port in suspicious_ports:
            return True
        
        # Check for multiple connections from same IP
        # (This would require tracking connection counts)
        
        return False
    
    def _log_suspicious(self, connection: Dict):
        """Log suspicious connection"""
        timestamp = datetime.now().isoformat()
        log_entry = (
            f"[{timestamp}] SUSPICIOUS CONNECTION: "
            f"{connection['remote_ip']}:{connection['remote_port']} -> "
            f"{connection['local_ip']}:{connection['local_port']}"
        )
        
        logger.warning(log_entry)
        
        # Log to file
        with open(self.connection_log, 'a') as f:
            f.write(log_entry + '\n')


def main():
    parser = argparse.ArgumentParser(
        description='LAN Device Discovery and Monitoring',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan network and discover devices
  python3 lan_monitor.py --scan-only
  
  # Scan and monitor for 5 minutes
  python3 lan_monitor.py --monitor-duration 300
  
  # Monitor specific suspicious IPs
  python3 lan_monitor.py --monitor-only --suspicious-ips 192.168.1.100,192.168.1.101
  
  # Use nmap for comprehensive scan
  python3 lan_monitor.py --scan-method nmap --scan-ports
        """
    )
    
    parser.add_argument('--interface', '-i', help='Network interface to use')
    parser.add_argument('--scan-only', action='store_true', help='Only scan network, do not monitor')
    parser.add_argument('--monitor-only', action='store_true', help='Only monitor, do not scan')
    parser.add_argument('--monitor-duration', '-d', type=int, default=0, 
                       help='Monitoring duration in seconds (0 = indefinite)')
    parser.add_argument('--scan-method', choices=['arp', 'ping', 'nmap'], default='ping',
                       help='Method to scan network (default: ping)')
    parser.add_argument('--scan-ports', action='store_true', help='Scan common ports on discovered devices')
    parser.add_argument('--suspicious-ips', help='Comma-separated list of IPs to monitor')
    parser.add_argument('--ncat-ports', help='Comma-separated list of ports to monitor with ncat')
    parser.add_argument('--output', '-o', default='lan_devices.json', help='Output file for device list')
    
    args = parser.parse_args()
    
    # Check if running as root (required for some operations)
    if os.geteuid() != 0:
        logger.warning("Not running as root. Some operations may fail.")
    
    # Parse suspicious IPs
    suspicious_ips = []
    if args.suspicious_ips:
        suspicious_ips = [ip.strip() for ip in args.suspicious_ips.split(',')]
    
    # Parse ncat ports
    ncat_ports = [80, 443, 8080, 8443, 22, 23, 21, 3389]
    if args.ncat_ports:
        ncat_ports = [int(port.strip()) for port in args.ncat_ports.split(',')]
    
    # Scan network
    if not args.monitor_only:
        logger.info("=" * 60)
        logger.info("LAN DEVICE DISCOVERY")
        logger.info("=" * 60)
        
        discovery = LANDiscovery(interface=args.interface)
        
        if not discovery.network_info:
            logger.error("Failed to get network information")
            sys.exit(1)
        
        # Scan network
        devices = discovery.scan_network(method=args.scan_method)
        
        # Scan ports if requested
        if args.scan_ports:
            logger.info("Scanning ports on discovered devices...")
            for ip in devices.keys():
                discovery.scan_ports(ip)
        
        # Save devices
        discovery.save_devices(args.output)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("SCAN SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Network: {discovery.network_info.network}/{discovery.network_info.netmask}")
        logger.info(f"Self IP: {discovery.self_ip}")
        logger.info(f"Devices found: {len(devices)}")
        
        for ip, device in devices.items():
            logger.info(f"  - {ip} ({device.mac}) - {device.hostname}")
            if device.open_ports:
                logger.info(f"    Open ports: {device.open_ports}")
        
        # Use discovered IPs as suspicious if not specified
        if not suspicious_ips and not args.monitor_only:
            suspicious_ips = list(devices.keys())
    
    # Monitor connections
    if not args.scan_only:
        logger.info("\n" + "=" * 60)
        logger.info("CONNECTION MONITORING")
        logger.info("=" * 60)
        
        # Get self IP
        if args.monitor_only:
            discovery = LANDiscovery(interface=args.interface)
            if not discovery.network_info:
                logger.error("Failed to get network information")
                sys.exit(1)
            self_ip = discovery.self_ip
        else:
            self_ip = discovery.self_ip
        
        # Monitor connections
        conn_monitor = ConnectionMonitor(self_ip)
        detected_suspicious = conn_monitor.monitor_connections(duration=args.monitor_duration)
        
        # Add detected suspicious IPs
        for ip in detected_suspicious:
            if ip not in suspicious_ips:
                suspicious_ips.append(ip)
        
        # Monitor with ncat
        if suspicious_ips:
            logger.info("\n" + "=" * 60)
            logger.info("NCAT MONITORING")
            logger.info("=" * 60)
            
            ncat_monitor = NcatMonitor(suspicious_ips, ncat_ports)
            ncat_monitor.start_monitoring(duration=args.monitor_duration)
        else:
            logger.info("No suspicious IPs to monitor")
    
    logger.info("\nMonitoring complete!")


if __name__ == '__main__':
    main()
