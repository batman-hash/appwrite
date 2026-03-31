#!/usr/bin/env python3
"""
MAC Address Rotation Script
Rotates MAC addresses on network interfaces at regular intervals
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
from typing import List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mac_rotation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MACRotator:
    """Handles MAC address rotation for network interfaces"""
    
    def __init__(self, interfaces: Optional[List[str]] = None, interval: int = 60):
        """
        Initialize MAC rotator
        
        Args:
            interfaces: List of interface names to rotate (None for all)
            interval: Rotation interval in seconds (default: 60)
        """
        self.interfaces = interfaces or self._get_interfaces()
        self.interval = interval
        self.running = False
        self.original_macs = {}
        
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
    
    def _generate_mac(self) -> str:
        """Generate a random MAC address"""
        # Generate random MAC with locally administered bit set
        # First octet: 0x02 (locally administered, unicast)
        mac = [0x02, 
               random.randint(0x00, 0x7f),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff),
               random.randint(0x00, 0xff)]
        
        return ':'.join(f'{b:02x}' for b in mac)
    
    def _get_current_mac(self, interface: str) -> Optional[str]:
        """Get current MAC address of an interface"""
        try:
            result = subprocess.run(
                ['ip', 'link', 'show', interface],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.split('\n'):
                if 'link/ether' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'link/ether' and i + 1 < len(parts):
                            return parts[i + 1]
            
            return None
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get MAC for {interface}: {e}")
            return None
    
    def _set_mac(self, interface: str, mac: str) -> bool:
        """Set MAC address on an interface"""
        try:
            # Bring interface down
            subprocess.run(
                ['ip', 'link', 'set', interface, 'down'],
                check=True,
                capture_output=True
            )
            
            # Set new MAC
            subprocess.run(
                ['ip', 'link', 'set', interface, 'address', mac],
                check=True,
                capture_output=True
            )
            
            # Bring interface up
            subprocess.run(
                ['ip', 'link', 'set', interface, 'up'],
                check=True,
                capture_output=True
            )
            
            logger.info(f"Changed MAC on {interface} to {mac}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to set MAC on {interface}: {e}")
            return False
    
    def rotate_once(self) -> bool:
        """Rotate MAC addresses once for all interfaces"""
        success = True
        
        for interface in self.interfaces:
            try:
                # Store original MAC if not already stored
                if interface not in self.original_macs:
                    original = self._get_current_mac(interface)
                    if original:
                        self.original_macs[interface] = original
                        logger.info(f"Stored original MAC for {interface}: {original}")
                
                # Generate and set new MAC
                new_mac = self._generate_mac()
                if self._set_mac(interface, new_mac):
                    logger.info(f"Rotated MAC on {interface}: {new_mac}")
                else:
                    success = False
                    
            except Exception as e:
                logger.error(f"Error rotating MAC on {interface}: {e}")
                success = False
        
        return success
    
    def restore_original(self) -> bool:
        """Restore original MAC addresses"""
        success = True
        
        for interface, original_mac in self.original_macs.items():
            try:
                if self._set_mac(interface, original_mac):
                    logger.info(f"Restored original MAC on {interface}: {original_mac}")
                else:
                    success = False
                    
            except Exception as e:
                logger.error(f"Error restoring MAC on {interface}: {e}")
                success = False
        
        return success
    
    def start(self):
        """Start continuous MAC rotation"""
        self.running = True
        logger.info(f"Starting MAC rotation every {self.interval} seconds")
        logger.info(f"Rotating interfaces: {self.interfaces}")
        
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
        """Stop MAC rotation and restore original MACs"""
        self.running = False
        logger.info("Stopping MAC rotation")
        
        # Restore original MACs
        if self.original_macs:
            logger.info("Restoring original MAC addresses")
            self.restore_original()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}")
        self.running = False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='MAC Address Rotation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Rotate all interfaces every 60 seconds
  python mac_rotation.py
  
  # Rotate specific interfaces every 30 seconds
  python mac_rotation.py -i eth0 wlan0 -t 30
  
  # Rotate once and exit
  python mac_rotation.py --once
  
  # Restore original MACs
  python mac_rotation.py --restore
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
        '--once',
        action='store_true',
        help='Rotate once and exit'
    )
    
    parser.add_argument(
        '--restore',
        action='store_true',
        help='Restore original MAC addresses'
    )
    
    args = parser.parse_args()
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        sys.exit(1)
    
    # Create rotator
    rotator = MACRotator(
        interfaces=args.interfaces,
        interval=args.interval
    )
    
    # Handle different modes
    if args.restore:
        if rotator.restore_original():
            logger.info("Successfully restored original MAC addresses")
            sys.exit(0)
        else:
            logger.error("Failed to restore some MAC addresses")
            sys.exit(1)
    
    elif args.once:
        if rotator.rotate_once():
            logger.info("Successfully rotated MAC addresses")
            sys.exit(0)
        else:
            logger.error("Failed to rotate some MAC addresses")
            sys.exit(1)
    
    else:
        # Continuous rotation
        rotator.start()


if __name__ == '__main__':
    main()
