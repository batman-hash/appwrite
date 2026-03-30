"""
TShark Integration Module

Provides integration with TShark for deep packet inspection and email extraction.
"""

import subprocess
import json
import re
import tempfile
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TSharkPacket:
    """TShark packet information"""
    frame_number: int
    timestamp: str
    source_ip: str
    destination_ip: str
    protocol: str
    length: int
    info: str
    layers: Dict[str, Any]


@dataclass
class TSharkFlow:
    """TShark network flow"""
    source_ip: str
    source_port: int
    destination_ip: str
    destination_port: int
    protocol: str
    packets: int
    bytes: int
    duration: float


class TSharkIntegration:
    """
    Integration with TShark for deep packet inspection.
    
    Features:
    - Live packet capture
    - PCAP file analysis
    - Email extraction from packets
    - Database protocol analysis
    - Network flow analysis
    """
    
    # Database protocol filters
    DATABASE_FILTERS = {
        'mongodb': 'tcp.port == 27017',
        'elasticsearch': 'tcp.port == 9200 || tcp.port == 9300',
        'redis': 'tcp.port == 6379',
        'mysql': 'tcp.port == 3306',
        'postgresql': 'tcp.port == 5432',
        'couchdb': 'tcp.port == 5984',
        'influxdb': 'tcp.port == 8086',
        'arangodb': 'tcp.port == 8529',
        'neo4j': 'tcp.port == 7474 || tcp.port == 7687',
        'cassandra': 'tcp.port == 9042',
        'memcached': 'tcp.port == 11211',
        'rethinkdb': 'tcp.port == 28015',
    }
    
    def __init__(self, tshark_path: str = 'tshark'):
        """
        Initialize TShark integration.
        
        Args:
            tshark_path: Path to tshark executable
        """
        self.tshark_path = tshark_path
    
    def check_tshark_installed(self) -> bool:
        """
        Check if TShark is installed.
        
        Returns:
            True if TShark is installed
        """
        try:
            result = subprocess.run(
                [self.tshark_path, '-v'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def capture_packets(
        self,
        interface: str = 'any',
        count: int = 100,
        filter_expr: Optional[str] = None,
        timeout: int = 30
    ) -> List[TSharkPacket]:
        """
        Capture packets from network interface.
        
        Args:
            interface: Network interface
            count: Number of packets to capture
            filter_expr: Display filter
            timeout: Capture timeout
            
        Returns:
            List of TSharkPacket objects
        """
        packets = []
        
        try:
            # Build command
            cmd = [
                self.tshark_path,
                '-i', interface,
                '-c', str(count),
                '-T', 'json',
            ]
            
            if filter_expr:
                cmd.extend(['-Y', filter_expr])
            
            # Run tshark
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Parse JSON output
            packets = self._parse_tshark_json(result.stdout)
            
        except subprocess.TimeoutExpired:
            print("Packet capture timed out")
        except Exception as e:
            print(f"Error capturing packets: {e}")
        
        return packets
    
    def analyze_pcap(
        self,
        pcap_file: str,
        filter_expr: Optional[str] = None
    ) -> List[TSharkPacket]:
        """
        Analyze PCAP file.
        
        Args:
            pcap_file: PCAP file path
            filter_expr: Display filter
            
        Returns:
            List of TSharkPacket objects
        """
        packets = []
        
        try:
            # Build command
            cmd = [
                self.tshark_path,
                '-r', pcap_file,
                '-T', 'json',
            ]
            
            if filter_expr:
                cmd.extend(['-Y', filter_expr])
            
            # Run tshark
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse JSON output
            packets = self._parse_tshark_json(result.stdout)
            
        except subprocess.TimeoutExpired:
            print("PCAP analysis timed out")
        except Exception as e:
            print(f"Error analyzing PCAP: {e}")
        
        return packets
    
    def _parse_tshark_json(self, json_output: str) -> List[TSharkPacket]:
        """
        Parse TShark JSON output.
        
        Args:
            json_output: TShark JSON output
            
        Returns:
            List of TSharkPacket objects
        """
        packets = []
        
        try:
            data = json.loads(json_output)
            
            for packet_data in data:
                # Extract packet information
                layers = packet_data.get('_source', {}).get('layers', {})
                
                # Get frame information
                frame = layers.get('frame', {})
                frame_number = int(frame.get('frame.number', 0))
                timestamp = frame.get('frame.time', '')
                length = int(frame.get('frame.len', 0))
                
                # Get IP information
                ip = layers.get('ip', {})
                source_ip = ip.get('ip.src', '')
                destination_ip = ip.get('ip.dst', '')
                
                # Get protocol
                protocol = frame.get('frame.protocols', '').split(':')[-1]
                
                # Get info
                info = frame.get('frame.info', '')
                
                packets.append(TSharkPacket(
                    frame_number=frame_number,
                    timestamp=timestamp,
                    source_ip=source_ip,
                    destination_ip=destination_ip,
                    protocol=protocol,
                    length=length,
                    info=info,
                    layers=layers
                ))
                
        except json.JSONDecodeError as e:
            print(f"Error parsing TShark JSON: {e}")
        except Exception as e:
            print(f"Error processing TShark output: {e}")
        
        return packets
    
    def extract_emails_from_pcap(
        self,
        pcap_file: str,
        database_type: Optional[str] = None
    ) -> List[str]:
        """
        Extract emails from PCAP file.
        
        Args:
            pcap_file: PCAP file path
            database_type: Database type to filter
            
        Returns:
            List of email addresses
        """
        emails = []
        
        # Build filter for database traffic
        filter_expr = None
        if database_type and database_type in self.DATABASE_FILTERS:
            filter_expr = self.DATABASE_FILTERS[database_type]
        
        # Analyze PCAP
        packets = self.analyze_pcap(pcap_file, filter_expr)
        
        # Extract emails from packets
        for packet in packets:
            # Search for emails in packet layers
            packet_emails = self._extract_emails_from_packet(packet)
            emails.extend(packet_emails)
        
        # Remove duplicates
        return list(set(emails))
    
    def _extract_emails_from_packet(self, packet: TSharkPacket) -> List[str]:
        """
        Extract emails from packet.
        
        Args:
            packet: TSharkPacket object
            
        Returns:
            List of email addresses
        """
        emails = []
        
        # Email regex pattern
        email_pattern = re.compile(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        )
        
        # Search in all layers
        for layer_name, layer_data in packet.layers.items():
            if isinstance(layer_data, dict):
                for key, value in layer_data.items():
                    if isinstance(value, str):
                        matches = email_pattern.findall(value)
                        emails.extend(matches)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                matches = email_pattern.findall(item)
                                emails.extend(matches)
        
        return emails
    
    def capture_database_traffic(
        self,
        interface: str = 'any',
        database_type: str = 'mongodb',
        count: int = 1000,
        timeout: int = 60
    ) -> List[TSharkPacket]:
        """
        Capture database traffic.
        
        Args:
            interface: Network interface
            database_type: Database type
            count: Number of packets to capture
            timeout: Capture timeout
            
        Returns:
            List of TSharkPacket objects
        """
        # Get filter for database type
        filter_expr = self.DATABASE_FILTERS.get(database_type)
        
        if not filter_expr:
            print(f"Unknown database type: {database_type}")
            return []
        
        # Capture packets
        return self.capture_packets(
            interface=interface,
            count=count,
            filter_expr=filter_expr,
            timeout=timeout
        )
    
    def analyze_database_traffic(
        self,
        pcap_file: str,
        database_type: str
    ) -> Dict[str, Any]:
        """
        Analyze database traffic in PCAP file.
        
        Args:
            pcap_file: PCAP file path
            database_type: Database type
            
        Returns:
            Dictionary containing analysis results
        """
        # Get filter for database type
        filter_expr = self.DATABASE_FILTERS.get(database_type)
        
        if not filter_expr:
            print(f"Unknown database type: {database_type}")
            return {}
        
        # Analyze PCAP
        packets = self.analyze_pcap(pcap_file, filter_expr)
        
        # Analyze traffic
        analysis = {
            'total_packets': len(packets),
            'total_bytes': sum(p.length for p in packets),
            'source_ips': {},
            'destination_ips': {},
            'protocols': {},
            'emails': [],
        }
        
        for packet in packets:
            # Count source IPs
            if packet.source_ip:
                analysis['source_ips'][packet.source_ip] = \
                    analysis['source_ips'].get(packet.source_ip, 0) + 1
            
            # Count destination IPs
            if packet.destination_ip:
                analysis['destination_ips'][packet.destination_ip] = \
                    analysis['destination_ips'].get(packet.destination_ip, 0) + 1
            
            # Count protocols
            if packet.protocol:
                analysis['protocols'][packet.protocol] = \
                    analysis['protocols'].get(packet.protocol, 0) + 1
            
            # Extract emails
            packet_emails = self._extract_emails_from_packet(packet)
            analysis['emails'].extend(packet_emails)
        
        # Remove duplicate emails
        analysis['emails'] = list(set(analysis['emails']))
        
        return analysis
    
    def extract_credentials_from_pcap(
        self,
        pcap_file: str,
        database_type: str
    ) -> List[Dict[str, str]]:
        """
        Extract credentials from PCAP file.
        
        Args:
            pcap_file: PCAP file path
            database_type: Database type
            
        Returns:
            List of credential dictionaries
        """
        credentials = []
        
        # Get filter for database type
        filter_expr = self.DATABASE_FILTERS.get(database_type)
        
        if not filter_expr:
            print(f"Unknown database type: {database_type}")
            return []
        
        # Analyze PCAP
        packets = self.analyze_pcap(pcap_file, filter_expr)
        
        # Extract credentials from packets
        for packet in packets:
            packet_creds = self._extract_credentials_from_packet(packet, database_type)
            credentials.extend(packet_creds)
        
        return credentials
    
    def _extract_credentials_from_packet(
        self,
        packet: TSharkPacket,
        database_type: str
    ) -> List[Dict[str, str]]:
        """
        Extract credentials from packet.
        
        Args:
            packet: TSharkPacket object
            database_type: Database type
            
        Returns:
            List of credential dictionaries
        """
        credentials = []
        
        # Look for authentication patterns
        for layer_name, layer_data in packet.layers.items():
            if isinstance(layer_data, dict):
                # Look for username/password patterns
                username = None
                password = None
                
                for key, value in layer_data.items():
                    if isinstance(value, str):
                        # Look for username
                        if 'user' in key.lower() or 'login' in key.lower():
                            username = value
                        # Look for password
                        elif 'pass' in key.lower() or 'pwd' in key.lower():
                            password = value
                
                if username and password:
                    credentials.append({
                        'username': username,
                        'password': password,
                        'source_ip': packet.source_ip,
                        'destination_ip': packet.destination_ip,
                        'timestamp': packet.timestamp,
                    })
        
        return credentials
    
    def get_network_flows(
        self,
        pcap_file: str,
        filter_expr: Optional[str] = None
    ) -> List[TSharkFlow]:
        """
        Get network flows from PCAP file.
        
        Args:
            pcap_file: PCAP file path
            filter_expr: Display filter
            
        Returns:
            List of TSharkFlow objects
        """
        flows = []
        
        try:
            # Build command
            cmd = [
                self.tshark_path,
                '-r', pcap_file,
                '-q', '-z', 'conv,tcp',
            ]
            
            if filter_expr:
                cmd.extend(['-Y', filter_expr])
            
            # Run tshark
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse flows
            flows = self._parse_flows(result.stdout)
            
        except subprocess.TimeoutExpired:
            print("Flow analysis timed out")
        except Exception as e:
            print(f"Error getting network flows: {e}")
        
        return flows
    
    def _parse_flows(self, output: str) -> List[TSharkFlow]:
        """
        Parse network flows from TShark output.
        
        Args:
            output: TShark output
            
        Returns:
            List of TSharkFlow objects
        """
        flows = []
        
        lines = output.split('\n')
        
        for line in lines:
            # Parse flow line
            # Format: <src_ip>:<src_port> <-> <dst_ip>:<dst_port> | <packets> | <bytes> | <duration>
            match = re.search(
                r'(\d+\.\d+\.\d+\.\d+):(\d+)\s+<->\s+(\d+\.\d+\.\d+\.\d+):(\d+)\s+\|\s+(\d+)\s+\|\s+(\d+)\s+\|\s+([\d.]+)',
                line
            )
            
            if match:
                src_ip, src_port, dst_ip, dst_port, packets, bytes_, duration = match.groups()
                
                flows.append(TSharkFlow(
                    source_ip=src_ip,
                    source_port=int(src_port),
                    destination_ip=dst_ip,
                    destination_port=int(dst_port),
                    protocol='tcp',
                    packets=int(packets),
                    bytes=int(bytes_),
                    duration=float(duration)
                ))
        
        return flows
