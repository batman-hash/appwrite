"""
CLI-Based Packet Capture Module

Provides packet capture by bridging to command-line tools (TShark, tcpdump).
Useful when Python libraries are not available or for leveraging existing tools.
"""

import os
import subprocess
import signal
import tempfile
import json
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from .packet_analyzer import PacketAnalyzer


@dataclass
class CliStats:
    """CLI capture statistics"""
    packets_captured: int = 0
    bytes_captured: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        """Calculate capture duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def packets_per_second(self) -> float:
        """Calculate packets per second"""
        duration = self.duration_seconds
        return self.packets_captured / duration if duration > 0 else 0.0


class CliCapture:
    """
    Packet capture using command-line tools (TShark, tcpdump).
    
    Features:
    - TShark capture (Wireshark's command-line tool)
    - tcpdump capture (standard Unix packet analyzer)
    - BPF filter support
    - PCAP file reading/writing
    - JSON output parsing (TShark)
    - Real-time packet processing
    
    Supported tools:
    - tshark: Part of Wireshark, powerful protocol analysis
    - tcpdump: Standard Unix packet capture tool
    """
    
    def __init__(
        self,
        interface: Optional[str] = None,
        tool: str = 'tshark'
    ):
        """
        Initialize CLI capture.
        
        Args:
            interface: Network interface to capture from
            tool: CLI tool to use ('tshark' or 'tcpdump')
        """
        self.interface = interface
        self.tool = tool.lower()
        
        self.analyzer = PacketAnalyzer()
        self.stats = CliStats()
        self.is_capturing = False
        self.captured_packets: List[Dict[str, Any]] = []
        self._callback: Optional[Callable] = None
        self._process: Optional[subprocess.Popen] = None
        
        # Validate tool availability
        self._validate_tool()
    
    def _validate_tool(self):
        """
        Validate that the specified tool is available.
        
        Raises:
            FileNotFoundError: If tool is not found
        """
        if self.tool == 'tshark':
            if not self._command_exists('tshark'):
                raise FileNotFoundError(
                    "tshark not found. Install with: apt-get install tshark"
                )
        elif self.tool == 'tcpdump':
            if not self._command_exists('tcpdump'):
                raise FileNotFoundError(
                    "tcpdump not found. Install with: apt-get install tcpdump"
                )
        else:
            raise ValueError(f"Unsupported tool: {self.tool}. Use 'tshark' or 'tcpdump'")
    
    @staticmethod
    def _command_exists(command: str) -> bool:
        """
        Check if a command exists in PATH.
        
        Args:
            command: Command name to check
            
        Returns:
            True if command exists, False otherwise
        """
        try:
            subprocess.run(
                ['which', command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _build_tshark_command(
        self,
        count: int = 0,
        filter_expr: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> List[str]:
        """
        Build tshark command.
        
        Args:
            count: Number of packets to capture
            filter_expr: BPF filter expression
            output_file: Output PCAP filename
            
        Returns:
            Command list
        """
        cmd = ['tshark']
        
        # Interface
        if self.interface:
            cmd.extend(['-i', self.interface])
        
        # Packet count
        if count > 0:
            cmd.extend(['-c', str(count)])
        
        # BPF filter
        if filter_expr:
            cmd.extend(['-f', filter_expr])
        
        # Output file
        if output_file:
            cmd.extend(['-w', output_file])
        
        # JSON output for parsing
        cmd.extend(['-T', 'json'])
        
        return cmd
    
    def _build_tcpdump_command(
        self,
        count: int = 0,
        filter_expr: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> List[str]:
        """
        Build tcpdump command.
        
        Args:
            count: Number of packets to capture
            filter_expr: BPF filter expression
            output_file: Output PCAP filename
            
        Returns:
            Command list
        """
        cmd = ['tcpdump']
        
        # Interface
        if self.interface:
            cmd.extend(['-i', self.interface])
        
        # Packet count
        if count > 0:
            cmd.extend(['-c', str(count)])
        
        # Don't resolve hostnames
        cmd.append('-n')
        
        # Verbose output
        cmd.append('-v')
        
        # BPF filter
        if filter_expr:
            cmd.append(filter_expr)
        
        # Output file
        if output_file:
            cmd.extend(['-w', output_file])
        
        return cmd
    
    def _parse_tshark_json(self, json_line: str) -> Optional[Dict[str, Any]]:
        """
        Parse tshark JSON output line.
        
        Args:
            json_line: JSON line from tshark
            
        Returns:
            Parsed packet dictionary or None
        """
        try:
            packet_data = json.loads(json_line)
            
            # Extract packet information
            layers = packet_data.get('_source', {}).get('layers', {})
            
            packet_info = {
                'packet_number': packet_data.get('_index', 0),
                'timestamp': packet_data.get('_source', {}).get('timestamp', ''),
                'raw_length': len(json_line),
                'protocols': [],
            }
            
            # Parse IP layer
            if 'ip' in layers:
                ip_layer = layers['ip']
                packet_info['protocols'].append('IP')
                packet_info['ip'] = {
                    'src_ip': ip_layer.get('ip.src', ''),
                    'dst_ip': ip_layer.get('ip.dst', ''),
                    'protocol': ip_layer.get('ip.proto', ''),
                    'ttl': ip_layer.get('ip.ttl', ''),
                }
            
            # Parse TCP layer
            if 'tcp' in layers:
                tcp_layer = layers['tcp']
                packet_info['protocols'].append('TCP')
                packet_info['tcp'] = {
                    'src_port': int(tcp_layer.get('tcp.srcport', 0)),
                    'dst_port': int(tcp_layer.get('tcp.dstport', 0)),
                    'flags': tcp_layer.get('tcp.flags', ''),
                    'seq': tcp_layer.get('tcp.seq', ''),
                    'ack': tcp_layer.get('tcp.ack', ''),
                }
            
            # Parse UDP layer
            if 'udp' in layers:
                udp_layer = layers['udp']
                packet_info['protocols'].append('UDP')
                packet_info['udp'] = {
                    'src_port': int(udp_layer.get('udp.srcport', 0)),
                    'dst_port': int(udp_layer.get('udp.dstport', 0)),
                    'length': udp_layer.get('udp.length', ''),
                }
            
            # Parse ICMP layer
            if 'icmp' in layers:
                icmp_layer = layers['icmp']
                packet_info['protocols'].append('ICMP')
                packet_info['icmp'] = {
                    'type': icmp_layer.get('icmp.type', ''),
                    'code': icmp_layer.get('icmp.code', ''),
                }
            
            # Parse HTTP layer
            if 'http' in layers:
                http_layer = layers['http']
                packet_info['protocols'].append('HTTP')
                packet_info['http'] = {
                    'method': http_layer.get('http.request.method', ''),
                    'host': http_layer.get('http.host', ''),
                    'path': http_layer.get('http.request.uri', ''),
                    'status': http_layer.get('http.response.code', ''),
                }
            
            return packet_info
            
        except json.JSONDecodeError:
            return None
        except Exception as e:
            print(f"Error parsing tshark JSON: {e}")
            return None
    
    def capture_tshark(
        self,
        count: int = 0,
        timeout: Optional[float] = None,
        filter_expr: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Capture packets using tshark.
        
        Args:
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
            filter_expr: BPF filter expression
            callback: Callback function for each packet
            
        Returns:
            List of captured packet dictionaries
        """
        if self.tool != 'tshark':
            raise ValueError("This method requires tshark tool")
        
        self.is_capturing = True
        self.stats.start_time = datetime.now()
        self._callback = callback
        
        try:
            # Build command
            cmd = self._build_tshark_command(count, filter_expr)
            
            # Start tshark process
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Read output line by line
            for line in self._process.stdout:
                if not self.is_capturing:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse JSON packet
                packet_info = self._parse_tshark_json(line)
                if packet_info:
                    # Update statistics
                    self.stats.packets_captured += 1
                    self.stats.bytes_captured += packet_info.get('raw_length', 0)
                    
                    # Store packet
                    self.captured_packets.append(packet_info)
                    
                    # Call callback if provided
                    if self._callback:
                        self._callback(packet_info)
            
            # Wait for process to complete
            self._process.wait()
            
        finally:
            self.is_capturing = False
            self.stats.end_time = datetime.now()
            
            if self._process:
                self._process.terminate()
                self._process = None
        
        return self.captured_packets
    
    def capture_tcpdump(
        self,
        count: int = 0,
        timeout: Optional[float] = None,
        filter_expr: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Capture packets using tcpdump.
        
        Args:
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
            filter_expr: BPF filter expression
            callback: Callback function for each packet
            
        Returns:
            List of captured packet dictionaries
        """
        if self.tool != 'tcpdump':
            raise ValueError("This method requires tcpdump tool")
        
        self.is_capturing = True
        self.stats.start_time = datetime.now()
        self._callback = callback
        
        try:
            # Build command
            cmd = self._build_tcpdump_command(count, filter_expr)
            
            # Start tcpdump process
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            # Read output line by line
            packet_buffer = []
            for line in self._process.stdout:
                if not self.is_capturing:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # tcpdump outputs one packet per line
                # Parse basic information
                packet_info = {
                    'packet_number': self.stats.packets_captured + 1,
                    'timestamp': datetime.now().isoformat(),
                    'raw_length': len(line),
                    'protocols': [],
                    'raw_output': line,
                }
                
                # Try to extract IP addresses
                import re
                ip_pattern = r'(\d+\.\d+\.\d+\.\d+)'
                ips = re.findall(ip_pattern, line)
                if len(ips) >= 2:
                    packet_info['protocols'].append('IP')
                    packet_info['ip'] = {
                        'src_ip': ips[0],
                        'dst_ip': ips[1],
                    }
                
                # Try to extract ports
                port_pattern = r'(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)'
                ports = re.findall(port_pattern, line)
                if ports:
                    src_port = int(ports[0][4])
                    dst_port = int(ports[1][4]) if len(ports) > 1 else 0
                    
                    if 'TCP' in line.upper():
                        packet_info['protocols'].append('TCP')
                        packet_info['tcp'] = {
                            'src_port': src_port,
                            'dst_port': dst_port,
                        }
                    elif 'UDP' in line.upper():
                        packet_info['protocols'].append('UDP')
                        packet_info['udp'] = {
                            'src_port': src_port,
                            'dst_port': dst_port,
                        }
                
                # Update statistics
                self.stats.packets_captured += 1
                self.stats.bytes_captured += len(line)
                
                # Store packet
                self.captured_packets.append(packet_info)
                
                # Call callback if provided
                if self._callback:
                    self._callback(packet_info)
            
            # Wait for process to complete
            self._process.wait()
            
        finally:
            self.is_capturing = False
            self.stats.end_time = datetime.now()
            
            if self._process:
                self._process.terminate()
                self._process = None
        
        return self.captured_packets
    
    def capture(
        self,
        count: int = 0,
        timeout: Optional[float] = None,
        filter_expr: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Capture packets using configured tool.
        
        Args:
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
            filter_expr: BPF filter expression
            callback: Callback function for each packet
            
        Returns:
            List of captured packet dictionaries
        """
        if self.tool == 'tshark':
            return self.capture_tshark(count, timeout, filter_expr, callback)
        elif self.tool == 'tcpdump':
            return self.capture_tcpdump(count, timeout, filter_expr, callback)
        else:
            raise ValueError(f"Unsupported tool: {self.tool}")
    
    def capture_to_file(
        self,
        filename: str,
        count: int = 0,
        timeout: Optional[float] = None,
        filter_expr: Optional[str] = None
    ) -> CliStats:
        """
        Capture packets to PCAP file.
        
        Args:
            filename: Output PCAP filename
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
            filter_expr: BPF filter expression
            
        Returns:
            Capture statistics
        """
        self.is_capturing = True
        self.stats.start_time = datetime.now()
        
        try:
            # Build command
            if self.tool == 'tshark':
                cmd = self._build_tshark_command(count, filter_expr, filename)
            else:
                cmd = self._build_tcpdump_command(count, filter_expr, filename)
            
            # Start process
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for completion or timeout
            try:
                self._process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                self._process.terminate()
            
            # Update statistics
            self.stats.packets_captured = count if count > 0 else 0
            
        finally:
            self.is_capturing = False
            self.stats.end_time = datetime.now()
            
            if self._process:
                self._process.terminate()
                self._process = None
        
        return self.stats
    
    def read_pcap(self, filename: str) -> List[Dict[str, Any]]:
        """
        Read packets from PCAP file.
        
        Args:
            filename: Input PCAP filename
            
        Returns:
            List of packet dictionaries
        """
        if self.tool == 'tshark':
            return self._read_pcap_tshark(filename)
        else:
            return self._read_pcap_tcpdump(filename)
    
    def _read_pcap_tshark(self, filename: str) -> List[Dict[str, Any]]:
        """Read PCAP file using tshark"""
        cmd = ['tshark', '-r', filename, '-T', 'json']
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse JSON output
            packets_data = json.loads(result.stdout)
            packets = []
            
            for packet_data in packets_data:
                packet_info = self._parse_tshark_json(json.dumps(packet_data))
                if packet_info:
                    packets.append(packet_info)
            
            self.captured_packets = packets
            self.stats.packets_captured = len(packets)
            
            return packets
            
        except subprocess.CalledProcessError as e:
            print(f"Error reading PCAP: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing tshark JSON: {e}")
            return []
    
    def _read_pcap_tcpdump(self, filename: str) -> List[Dict[str, Any]]:
        """Read PCAP file using tcpdump"""
        cmd = ['tcpdump', '-r', filename, '-n', '-v']
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse tcpdump output
            packets = []
            for line in result.stdout.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                packet_info = {
                    'packet_number': len(packets) + 1,
                    'timestamp': datetime.now().isoformat(),
                    'raw_length': len(line),
                    'protocols': [],
                    'raw_output': line,
                }
                
                packets.append(packet_info)
            
            self.captured_packets = packets
            self.stats.packets_captured = len(packets)
            
            return packets
            
        except subprocess.CalledProcessError as e:
            print(f"Error reading PCAP: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get capture statistics.
        
        Returns:
            Dictionary containing capture statistics
        """
        return {
            'packets_captured': self.stats.packets_captured,
            'bytes_captured': self.stats.bytes_captured,
            'duration_seconds': self.stats.duration_seconds,
            'packets_per_second': self.stats.packets_per_second,
            'is_capturing': self.is_capturing,
            'interface': self.interface,
            'tool': self.tool,
        }
    
    def stop_capture(self):
        """Stop ongoing capture"""
        self.is_capturing = False
        
        if self._process:
            self._process.terminate()
            self._process = None
    
    def clear_captured(self):
        """Clear captured packets list"""
        self.captured_packets.clear()
        self.stats = CliStats()
        self.analyzer = PacketAnalyzer()
