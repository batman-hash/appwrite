#!/usr/bin/env python3
"""
IP Address Rotation Script
Rotates IP addresses on network interfaces at regular intervals
for privacy and security purposes.
"""

import os
import sys
import subprocess
import random
import time
import logging
import signal
import argparse
import ipaddress
from typing import List, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ip_rotation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IPRotator:
    """Handles IP address rotation for network interfaces"""
    
    def __init__(self, 
                 interfaces: Optional[List[str]] = None, 
                 interval: int = 60,
                 subnet: str = "192.168.1.0/24",
                 gateway: Optional[str] = None):
        """
        Initialize IP rotator
        
        Args:
            interfaces: List of interface names to rotate (None for all)
            interval: Rotation interval in seconds (default: 60)
            subnet: Subnet to use for IP generation (default: 192.168.1.0/24)
            gateway: Gateway IP address (default: first usable IP in subnet)
        """
        self.interfaces = interfaces or self._get_interfaces()
        self.interval = interval
        self.subnet = ipaddress.IPv4Network(subnet)
        self.gateway = gateway or str(list(self.subnet.hosts())[0])
        self.running = False
        self.original_ips = {}
        self.current_ips = {}
        
    def _get_interfaces(self) -> List[str]:
        """Get list of available network interfaces"""
        try:
            result = subprocess.run(
                ['ip', 'link', 'show'],
                capture_output=True,
                text=True,
                check=True
            )
            
            interfaces = []
            for line in result.stdout.split('\n'):
                if ': ' in line and 'state' in line.lower():
                    # Extract interface name (e.g., "eth0:", "wlan0:")
                    parts = line.split(': ')
                    if len(parts) >= 2:
                        iface = parts[1].split(':')[0]
                        # Skip loopback and docker interfaces
                        if iface != 'lo' and not iface.startswith('docker') and not iface.startswith('veth'):
                            interfaces.append(iface)
            
            logger.info(f"Found interfaces: {interfaces}")
            return interfaces
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get interfaces: {e}")
            return []
    
    def _generate_ip(self) -> str:
        """Generate a random IP address within the subnet"""
        # Get all usable hosts in the subnet (excluding network and broadcast)
        hosts = list(self.subnet.hosts())
        
        # Skip the gateway IP
        available_hosts = [h for h in hosts if str(h) != self.gateway]
        
        if not available_hosts:
            raise ValueError(f"No available hosts in subnet {self.subnet}")
        
        # Select random IP
        return str(random.choice(available_hosts))
    
    def _get_current_ip(self, interface: str) -> Optional[str]:
        """Get current IP address of an interface"""
        try:
            result = subprocess.run(
                ['ip', 'addr', 'show', interface],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.split('\n'):
                if 'inet ' in line and 'scope global' in line:
                    # Extract IP address (e.g., "inet 192.168.1.50/24")
                    parts = line.strip().split()
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            return parts[i + 1].split('/')[0]
            
            return None
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get IP for {interface}: {e}")
            return None
    
    def _get_current_cidr(self, interface: str) -> Optional[str]:
        """Get current IP address with CIDR notation"""
        try:
            result = subprocess.run(
                ['ip', 'addr', 'show', interface],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.split('\n'):
                if 'inet ' in line and 'scope global' in line:
                    # Extract IP address with CIDR (e.g., "192.168.1.50/24")
                    parts = line.strip().split()
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            return parts[i + 1]
            
            return None
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get CIDR for {interface}: {e}")
            return None
    
    def _remove_ip(self, interface: str, ip_cidr: str) -> bool:
        """Remove an IP address from an interface"""
        try:
            subprocess.run(
                ['ip', 'addr', 'del', ip_cidr, 'dev', interface],
                check=True,
                capture_output=True
            )
            
            logger.info(f"Removed IP {ip_cidr} from {interface}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to remove IP from {interface}: {e}")
            return False
    
    def _add_ip(self, interface: str, ip_cidr: str) -> bool:
        """Add an IP address to an interface"""
        try:
            subprocess.run(
                ['ip', 'addr', 'add', ip_cidr, 'dev', interface],
                check=True,
                capture_output=True
            )
            
            logger.info(f"Added IP {ip_cidr} to {interface}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to add IP to {interface}: {e}")
            return False
    
    def _set_gateway(self, interface: str) -> bool:
        """Set the default gateway for an interface"""
        try:
            # Remove existing default route
            subprocess.run(
                ['ip', 'route', 'del', 'default'],
                capture_output=True
            )
            
            # Add new default route
            subprocess.run(
                ['ip', 'route', 'add', 'default', 'via', self.gateway, 'dev', interface],
                check=True,
                capture_output=True
            )
            
            logger.info(f"Set default gateway to {self.gateway} via {interface}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set gateway: {e}")
            return False
    
    def rotate_once(self) -> bool:
        """Rotate IP addresses once for all interfaces"""
        success = True
        
        for interface in self.interfaces:
            try:
                # Store original IP if not already stored
                if interface not in self.original_ips:
                    original_cidr = self._get_current_cidr(interface)
                    if original_cidr:
                        self.original_ips[interface] = original_cidr
                        logger.info(f"Stored original IP for {interface}: {original_cidr}")
                
                # Get current IP
                current_cidr = self._get_current_cidr(interface)
                
                # Generate new IP
                new_ip = self._generate_ip()
                new_cidr = f"{new_ip}/{self.subnet.prefixlen}"
                
                # Remove old IP if exists
                if current_cidr:
                    if not self._remove_ip(interface, current_cidr):
                        success = False
                
                # Add new IP
                if self._add_ip(interface, new_cidr):
                    self.current_ips[interface] = new_cidr
                    logger.info(f"Rotated IP on {interface}: {new_cidr}")
                    
                    # Set gateway
                    self._set_gateway(interface)
                else:
                    success = False
                    
            except Exception as e:
                logger.error(f"Error rotating IP on {interface}: {e}")
                success = False
        
        return success
    
    def restore_original(self) -> bool:
        """Restore original IP addresses"""
        success = True
        
        for interface, original_cidr in self.original_ips.items():
            try:
                # Get current IP
                current_cidr = self._get_current_cidr(interface)
                
                # Remove current IP if exists
                if current_cidr:
                    self._remove_ip(interface, current_cidr)
                
                # Add original IP
                if self._add_ip(interface, original_cidr):
                    logger.info(f"Restored original IP on {interface}: {original_cidr}")
                else:
                    success = False
                    
            except Exception as e:
                logger.error(f"Error restoring IP on {interface}: {e}")
                success = False
        
        return success
    
    def start(self):
        """Start continuous IP rotation"""
        self.running = True
        logger.info(f"Starting IP rotation every {self.interval} seconds")
        logger.info(f"Rotating interfaces: {self.interfaces}")
        logger.info(f"Using subnet: {self.subnet}")
        logger.info(f"Using gateway: {self.gateway}")
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            while self.running:
                self.rotate_once()
                
                # Wait for next rotation
                for _ in range(self.interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.stop()
    
    def stop(self):
        """Stop IP rotation and restore original IPs"""
        self.running = False
        logger.info("Stopping IP rotation")
        
        # Restore original IPs
        if self.original_ips:
            logger.info("Restoring original IP addresses")
            self.restore_original()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.running = False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='IP Address Rotation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Rotate all interfaces every 60 seconds
  python ip_rotation.py
  
  # Rotate specific interfaces every 30 seconds
  python ip_rotation.py -i eth0 wlan0 -t 30
  
  # Use custom subnet
  python ip_rotation.py --subnet 10.0.0.0/24
  
  # Use custom gateway
  python ip_rotation.py --gateway 192.168.1.1
  
  # Rotate once and exit
  python ip_rotation.py --once
  
  # Restore original IPs
  python ip_rotation.py --restore
        """
    )
    
    parser.add_argument(
        '-i', '--interfaces',
        nargs='+',
        help='Network interfaces to rotate (default: all)'
    )
    
    parser.add_argument(
        '-t', '--interval',
        type=int,
        default=60,
        help='Rotation interval in seconds (default: 60)'
    )
    
    parser.add_argument(
        '-s', '--subnet',
        default='192.168.1.0/24',
        help='Subnet to use for IP generation (default: 192.168.1.0/24)'
    )
    
    parser.add_argument(
        '-g', '--gateway',
        help='Gateway IP address (default: first usable IP in subnet)'
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Rotate once and exit'
    )
    
    parser.add_argument(
        '--restore',
        action='store_true',
        help='Restore original IP addresses'
    )
    
    args = parser.parse_args()
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        sys.exit(1)
    
    # Create rotator
    rotator = IPRotator(
        interfaces=args.interfaces,
        interval=args.interval,
        subnet=args.subnet,
        gateway=args.gateway
    )
    
    # Handle different modes
    if args.restore:
        if rotator.restore_original():
            logger.info("Successfully restored original IP addresses")
            sys.exit(0)
        else:
            logger.error("Failed to restore some IP addresses")
            sys.exit(1)
    
    elif args.once:
        if rotator.rotate_once():
            logger.info("Successfully rotated IP addresses")
            sys.exit(0)
        else:
            logger.error("Failed to rotate some IP addresses")
            sys.exit(1)
    
    else:
        # Continuous rotation
        rotator.start()


if __name__ == '__main__':
    main()
