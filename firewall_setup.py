#!/usr/bin/env python3
"""
Firewall Setup Script
Configures iptables rules to block sniffers, injection attacks,
disable file transfers between devices, and block remote ports.
"""

import os
import sys
import subprocess
import logging
import argparse
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('firewall_setup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FirewallSetup:
    """Configures firewall rules for network security"""
    
    def __init__(self, interface: Optional[str] = None):
        """
        Initialize firewall setup
        
        Args:
            interface: Network interface to apply rules to (None for all)
        """
        self.interface = interface
        self.rules_applied = []
        
    def _run_command(self, cmd: List[str], check: bool = True) -> bool:
        """Run a shell command"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=check
            )
            if result.returncode == 0:
                logger.info(f"Command succeeded: {' '.join(cmd)}")
                return True
            else:
                logger.warning(f"Command failed: {' '.join(cmd)}")
                logger.warning(f"Error: {result.stderr}")
                return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Command error: {' '.join(cmd)}")
            logger.error(f"Error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
    
    def flush_rules(self) -> bool:
        """Flush all existing iptables rules"""
        logger.info("Flushing existing iptables rules...")
        
        commands = [
            ["iptables", "-F"],
            ["iptables", "-X"],
            ["iptables", "-t", "nat", "-F"],
            ["iptables", "-t", "nat", "-X"],
            ["iptables", "-t", "mangle", "-F"],
            ["iptables", "-t", "mangle", "-X"],
        ]
        
        success = True
        for cmd in commands:
            if not self._run_command(cmd, check=False):
                success = False
        
        return success
    
    def set_default_policies(self) -> bool:
        """Set default policies to DROP"""
        logger.info("Setting default policies to DROP...")
        
        commands = [
            ["iptables", "-P", "INPUT", "DROP"],
            ["iptables", "-P", "FORWARD", "DROP"],
            ["iptables", "-P", "OUTPUT", "DROP"],
        ]
        
        success = True
        for cmd in commands:
            if not self._run_command(cmd):
                success = False
        
        return success
    
    def allow_loopback(self) -> bool:
        """Allow loopback traffic"""
        logger.info("Allowing loopback traffic...")
        
        commands = [
            ["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"],
            ["iptables", "-A", "OUTPUT", "-o", "lo", "-j", "ACCEPT"],
        ]
        
        success = True
        for cmd in commands:
            if not self._run_command(cmd):
                success = False
        
        return success
    
    def allow_established_connections(self) -> bool:
        """Allow established and related connections"""
        logger.info("Allowing established connections...")
        
        commands = [
            ["iptables", "-A", "INPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
            ["iptables", "-A", "OUTPUT", "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"],
        ]
        
        success = True
        for cmd in commands:
            if not self._run_command(cmd):
                success = False
        
        return success
    
    def block_sniffing(self) -> bool:
        """Block common sniffing attempts"""
        logger.info("Blocking sniffing attempts...")
        
        # Block ARP spoofing attempts
        commands = [
            # Drop packets with invalid TCP flags
            ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "ALL", "ALL", "-j", "DROP"],
            ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "ALL", "NONE", "-j", "DROP"],
            
            # Drop XMAS packets
            ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "ALL", "FIN,URG,PSH", "-j", "DROP"],
            
            # Drop NULL packets
            ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "ALL", "NONE", "-j", "DROP"],
            
            # Block port scanning
            ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "SYN,ACK,SYN", "SYN", "-j", "DROP"],
            
            # Block SYN flood attacks
            ["iptables", "-A", "INPUT", "-p", "tcp", "--syn", "-m", "limit", "--limit", "1/s", "--limit-burst", "3", "-j", "ACCEPT"],
            ["iptables", "-A", "INPUT", "-p", "tcp", "--syn", "-j", "DROP"],
        ]
        
        success = True
        for cmd in commands:
            if not self._run_command(cmd, check=False):
                success = False
        
        return success
    
    def block_injection_attacks(self) -> bool:
        """Block injection attacks"""
        logger.info("Blocking injection attacks...")
        
        # Block ICMP redirect attacks
        commands = [
            ["iptables", "-A", "INPUT", "-p", "icmp", "--icmp-type", "redirect", "-j", "DROP"],
            ["iptables", "-A", "OUTPUT", "-p", "icmp", "--icmp-type", "redirect", "-j", "DROP"],
            
            # Block source routing
            ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-option", "all", "-j", "DROP"],
            
            # Block malformed packets
            ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "SYN,FIN", "SYN,FIN", "-j", "DROP"],
            ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "SYN,RST", "SYN,RST", "-j", "DROP"],
            ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "FIN,RST", "FIN,RST", "-j", "DROP"],
            ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "ACK,FIN", "FIN", "-j", "DROP"],
            ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "ACK,URG", "URG", "-j", "DROP"],
            ["iptables", "-A", "INPUT", "-p", "tcp", "--tcp-flags", "ACK,PSH", "PSH", "-j", "DROP"],
        ]
        
        success = True
        for cmd in commands:
            if not self._run_command(cmd, check=False):
                success = False
        
        return success
    
    def disable_file_transfers(self) -> bool:
        """Disable file transfers between devices"""
        logger.info("Disabling file transfers between devices...")
        
        # Block SMB/CIFS (Windows file sharing)
        commands = [
            ["iptables", "-A", "INPUT", "-p", "tcp", "--dport", "445", "-j", "DROP"],
            ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "445", "-j", "DROP"],
            ["iptables", "-A", "INPUT", "-p", "tcp", "--dport", "139", "-j", "DROP"],
            ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "139", "-j", "DROP"],
            
            # Block NFS (Unix file sharing)
            ["iptables", "-A", "INPUT", "-p", "tcp", "--dport", "2049", "-j", "DROP"],
            ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "2049", "-j", "DROP"],
            
            # Block FTP
            ["iptables", "-A", "INPUT", "-p", "tcp", "--dport", "21", "-j", "DROP"],
            ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "21", "-j", "DROP"],
            
            # Block TFTP
            ["iptables", "-A", "INPUT", "-p", "udp", "--dport", "69", "-j", "DROP"],
            ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "69", "-j", "DROP"],
            
            # Block SCP/SFTP (SSH file transfer)
            ["iptables", "-A", "INPUT", "-p", "tcp", "--dport", "22", "-j", "DROP"],
            ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "22", "-j", "DROP"],
            
            # Block rsync
            ["iptables", "-A", "INPUT", "-p", "tcp", "--dport", "873", "-j", "DROP"],
            ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "873", "-j", "DROP"],
            
            # Block HTTP/HTTPS file uploads
            ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "80", "-m", "string", "--string", "POST", "--algo", "bm", "-j", "DROP"],
            ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "443", "-m", "string", "--string", "POST", "--algo", "bm", "-j", "DROP"],
        ]
        
        success = True
        for cmd in commands:
            if not self._run_command(cmd, check=False):
                success = False
        
        return success
    
    def block_remote_ports(self) -> bool:
        """Block all remote ports except essential ones"""
        logger.info("Blocking remote ports...")
        
        # Allow DNS (port 53)
        commands = [
            ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "53", "-j", "ACCEPT"],
            ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "53", "-j", "ACCEPT"],
            
            # Allow DHCP (ports 67, 68)
            ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "67", "-j", "ACCEPT"],
            ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "68", "-j", "ACCEPT"],
            
            # Allow NTP (port 123)
            ["iptables", "-A", "OUTPUT", "-p", "udp", "--dport", "123", "-j", "ACCEPT"],
            
            # Block all other outgoing traffic
            ["iptables", "-A", "OUTPUT", "-j", "DROP"],
        ]
        
        success = True
        for cmd in commands:
            if not self._run_command(cmd, check=False):
                success = False
        
        return success
    
    def allow_web_access(self) -> bool:
        """Allow web access (HTTP/HTTPS)"""
        logger.info("Allowing web access...")
        
        commands = [
            ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "80", "-j", "ACCEPT"],
            ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", "443", "-j", "ACCEPT"],
        ]
        
        success = True
        for cmd in commands:
            if not self._run_command(cmd):
                success = False
        
        return success
    
    def allow_specific_ports(self, ports: List[int]) -> bool:
        """Allow specific ports"""
        logger.info(f"Allowing specific ports: {ports}")
        
        success = True
        for port in ports:
            cmd = ["iptables", "-A", "OUTPUT", "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"]
            if not self._run_command(cmd):
                success = False
        
        return success
    
    def block_lan_communication(self) -> bool:
        """Block communication between devices on LAN"""
        logger.info("Blocking LAN communication...")
        
        # Block all traffic to/from private IP ranges
        private_ranges = [
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16",
        ]
        
        success = True
        for ip_range in private_ranges:
            # Block incoming from LAN
            cmd = ["iptables", "-A", "INPUT", "-s", ip_range, "-j", "DROP"]
            if not self._run_command(cmd, check=False):
                success = False
            
            # Block outgoing to LAN
            cmd = ["iptables", "-A", "OUTPUT", "-d", ip_range, "-j", "DROP"]
            if not self._run_command(cmd, check=False):
                success = False
        
        return success
    
    def apply_all_rules(self, allow_web: bool = True, allow_ports: Optional[List[int]] = None) -> bool:
        """Apply all firewall rules"""
        logger.info("Applying all firewall rules...")
        
        success = True
        
        # Flush existing rules
        if not self.flush_rules():
            success = False
        
        # Set default policies
        if not self.set_default_policies():
            success = False
        
        # Allow loopback
        if not self.allow_loopback():
            success = False
        
        # Allow established connections
        if not self.allow_established_connections():
            success = False
        
        # Block sniffing
        if not self.block_sniffing():
            success = False
        
        # Block injection attacks
        if not self.block_injection_attacks():
            success = False
        
        # Disable file transfers
        if not self.disable_file_transfers():
            success = False
        
        # Block LAN communication
        if not self.block_lan_communication():
            success = False
        
        # Block remote ports
        if not self.block_remote_ports():
            success = False
        
        # Allow web access if requested
        if allow_web:
            if not self.allow_web_access():
                success = False
        
        # Allow specific ports if provided
        if allow_ports:
            if not self.allow_specific_ports(allow_ports):
                success = False
        
        if success:
            logger.info("All firewall rules applied successfully")
        else:
            logger.warning("Some firewall rules failed to apply")
        
        return success
    
    def save_rules(self, path: str = "/etc/iptables/rules.v4") -> bool:
        """Save iptables rules to file"""
        logger.info(f"Saving rules to {path}...")
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Save rules
            cmd = ["iptables-save", ">", path]
            result = subprocess.run(
                " ".join(cmd),
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Rules saved to {path}")
                return True
            else:
                logger.error(f"Failed to save rules: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error saving rules: {e}")
            return False
    
    def restore_rules(self, path: str = "/etc/iptables/rules.v4") -> bool:
        """Restore iptables rules from file"""
        logger.info(f"Restoring rules from {path}...")
        
        try:
            if not os.path.exists(path):
                logger.error(f"Rules file not found: {path}")
                return False
            
            cmd = ["iptables-restore", "<", path]
            result = subprocess.run(
                " ".join(cmd),
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Rules restored from {path}")
                return True
            else:
                logger.error(f"Failed to restore rules: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error restoring rules: {e}")
            return False
    
    def show_rules(self) -> bool:
        """Show current iptables rules"""
        logger.info("Showing current iptables rules...")
        
        try:
            cmd = ["iptables", "-L", "-v", "-n"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                logger.error(f"Failed to show rules: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error showing rules: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Firewall Setup Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply all rules (block sniffers, injection, file transfers, remote ports)
  sudo python firewall_setup.py --apply
  
  # Apply rules and allow web access
  sudo python firewall_setup.py --apply --allow-web
  
  # Apply rules and allow specific ports
  sudo python firewall_setup.py --apply --allow-ports 8080 3000
  
  # Show current rules
  sudo python firewall_setup.py --show
  
  # Save rules to file
  sudo python firewall_setup.py --save
  
  # Restore rules from file
  sudo python firewall_setup.py --restore
  
  # Flush all rules
  sudo python firewall_setup.py --flush
        """
    )
    
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply all firewall rules'
    )
    
    parser.add_argument(
        '--allow-web',
        action='store_true',
        help='Allow web access (HTTP/HTTPS)'
    )
    
    parser.add_argument(
        '--allow-ports',
        nargs='+',
        type=int,
        help='Allow specific ports'
    )
    
    parser.add_argument(
        '--show',
        action='store_true',
        help='Show current iptables rules'
    )
    
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save rules to /etc/iptables/rules.v4'
    )
    
    parser.add_argument(
        '--restore',
        action='store_true',
        help='Restore rules from /etc/iptables/rules.v4'
    )
    
    parser.add_argument(
        '--flush',
        action='store_true',
        help='Flush all iptables rules'
    )
    
    parser.add_argument(
        '-i', '--interface',
        help='Network interface to apply rules to'
    )
    
    args = parser.parse_args()
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        sys.exit(1)
    
    # Create firewall setup
    firewall = FirewallSetup(interface=args.interface)
    
    # Handle different modes
    if args.apply:
        if firewall.apply_all_rules(allow_web=args.allow_web, allow_ports=args.allow_ports):
            logger.info("Firewall rules applied successfully")
            sys.exit(0)
        else:
            logger.error("Failed to apply some firewall rules")
            sys.exit(1)
    
    elif args.show:
        if firewall.show_rules():
            sys.exit(0)
        else:
            sys.exit(1)
    
    elif args.save:
        if firewall.save_rules():
            logger.info("Rules saved successfully")
            sys.exit(0)
        else:
            logger.error("Failed to save rules")
            sys.exit(1)
    
    elif args.restore:
        if firewall.restore_rules():
            logger.info("Rules restored successfully")
            sys.exit(0)
        else:
            logger.error("Failed to restore rules")
            sys.exit(1)
    
    elif args.flush:
        if firewall.flush_rules():
            logger.info("Rules flushed successfully")
            sys.exit(0)
        else:
            logger.error("Failed to flush rules")
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
