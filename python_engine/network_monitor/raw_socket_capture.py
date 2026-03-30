"""
Raw Socket Packet Capture Module

Provides low-level packet capture using raw sockets (AF_PACKET, SOCK_RAW).
This is Linux-specific and provides direct access to Layer 2 (Ethernet) frames.
"""

import socket
import struct
import time
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field

from .packet_analyzer import PacketAnalyzer


@dataclass
class RawSocketStats:
    """Raw socket capture statistics"""
    packets_captured: int = 0
    bytes_captured: int = 0
    packets_dropped: int = 0
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


class RawSocketCapture:
    """
    Low-level packet capture using raw sockets.
    
    Features:
    - Direct Layer 2 (Ethernet) frame access
    - Linux-specific AF_PACKET interface
    - Captures all Ethernet-based traffic
    - Manual header parsing required
    - High performance with minimal overhead
    
    Note:
        Requires root privileges or CAP_NET_RAW capability
        Linux-specific (AF_PACKET is not available on Windows/macOS)
    """
    
    # Socket protocol constants
    ETH_P_ALL = 0x0003  # All protocols
    ETH_P_IP = 0x0800   # Internet Protocol
    ETH_P_ARP = 0x0806  # Address Resolution Protocol
    
    def __init__(
        self,
        interface: Optional[str] = None,
        buffer_size: int = 65535
    ):
        """
        Initialize raw socket capture.
        
        Args:
            interface: Network interface to capture from (e.g., 'eth0', 'wlan0')
                      If None, captures from all interfaces
            buffer_size: Socket buffer size in bytes (default: 65535 for jumbo frames)
        """
        self.interface = interface
        self.buffer_size = buffer_size
        self.socket: Optional[socket.socket] = None
        self.analyzer = PacketAnalyzer()
        self.stats = RawSocketStats()
        self.is_capturing = False
        self.captured_packets: List[Dict[str, Any]] = []
        self._callback: Optional[Callable] = None
    
    def _create_socket(self) -> socket.socket:
        """
        Create raw socket for packet capture.
        
        Returns:
            Configured raw socket
            
        Raises:
            PermissionError: If not running as root or without CAP_NET_RAW
            OSError: If socket creation fails
        """
        try:
            # Create raw socket
            # AF_PACKET: Linux-specific, direct access to Layer 2
            # SOCK_RAW: Raw packets including headers
            # ETH_P_ALL: Capture all Ethernet protocols
            sock = socket.socket(
                socket.AF_PACKET,
                socket.SOCK_RAW,
                socket.htons(self.ETH_P_ALL)
            )
            
            # Bind to specific interface if specified
            if self.interface:
                sock.bind((self.interface, 0))
            
            return sock
            
        except PermissionError:
            raise PermissionError(
                "Root privileges required for raw socket capture. "
                "Run with sudo or grant CAP_NET_RAW capability."
            )
        except OSError as e:
            raise OSError(f"Failed to create raw socket: {e}")
    
    def capture(
        self,
        count: int = 0,
        timeout: Optional[float] = None,
        callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Capture packets from network interface.
        
        Args:
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
            callback: Callback function for each packet
            
        Returns:
            List of captured packet dictionaries
        """
        self.is_capturing = True
        self.stats.start_time = datetime.now()
        self._callback = callback
        
        try:
            self.socket = self._create_socket()
            
            packets_captured = 0
            start_time = time.time()
            
            while self.is_capturing:
                # Check packet count limit
                if count > 0 and packets_captured >= count:
                    break
                
                # Check timeout
                if timeout and (time.time() - start_time) >= timeout:
                    break
                
                try:
                    # Receive raw packet
                    raw_data, addr = self.socket.recvfrom(self.buffer_size)
                    
                    # Parse packet
                    packet_info = self.analyzer.analyze_packet(raw_data)
                    packet_info['raw_data'] = raw_data
                    packet_info['interface'] = addr[0] if addr else self.interface
                    
                    # Update statistics
                    self.stats.packets_captured += 1
                    self.stats.bytes_captured += len(raw_data)
                    packets_captured += 1
                    
                    # Store packet
                    self.captured_packets.append(packet_info)
                    
                    # Call callback if provided
                    if self._callback:
                        self._callback(packet_info)
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error capturing packet: {e}")
                    self.stats.packets_dropped += 1
                    continue
                    
        finally:
            self.is_capturing = False
            self.stats.end_time = datetime.now()
            
            if self.socket:
                self.socket.close()
                self.socket = None
        
        return self.captured_packets
    
    def capture_continuous(
        self,
        callback: Callable,
        filter_func: Optional[Callable] = None
    ):
        """
        Capture packets continuously with callback.
        
        Args:
            callback: Callback function for each packet
            filter_func: Optional filter function to apply to packets
        """
        self.is_capturing = True
        self.stats.start_time = datetime.now()
        self._callback = callback
        
        try:
            self.socket = self._create_socket()
            
            while self.is_capturing:
                try:
                    raw_data, addr = self.socket.recvfrom(self.buffer_size)
                    
                    # Parse packet
                    packet_info = self.analyzer.analyze_packet(raw_data)
                    packet_info['raw_data'] = raw_data
                    packet_info['interface'] = addr[0] if addr else self.interface
                    
                    # Apply filter if provided
                    if filter_func and not filter_func(packet_info):
                        continue
                    
                    # Update statistics
                    self.stats.packets_captured += 1
                    self.stats.bytes_captured += len(raw_data)
                    
                    # Store packet
                    self.captured_packets.append(packet_info)
                    
                    # Call callback
                    self._callback(packet_info)
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error capturing packet: {e}")
                    self.stats.packets_dropped += 1
                    continue
                    
        finally:
            self.is_capturing = False
            self.stats.end_time = datetime.now()
            
            if self.socket:
                self.socket.close()
                self.socket = None
    
    def filter_packets(
        self,
        packets: Optional[List[Dict[str, Any]]] = None,
        protocol: Optional[str] = None,
        src_ip: Optional[str] = None,
        dst_ip: Optional[str] = None,
        src_port: Optional[int] = None,
        dst_port: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter captured packets by various criteria.
        
        Args:
            packets: List of packets to filter (uses captured_packets if None)
            protocol: Protocol to filter ('tcp', 'udp', 'icmp')
            src_ip: Source IP address
            dst_ip: Destination IP address
            src_port: Source port number
            dst_port: Destination port number
            
        Returns:
            Filtered list of packets
        """
        if packets is None:
            packets = self.captured_packets
        
        filtered = packets
        
        # Filter by protocol
        if protocol:
            protocol = protocol.lower()
            filtered = [
                p for p in filtered
                if protocol in [proto.lower() for proto in p.get('protocols', [])]
            ]
        
        # Filter by source IP
        if src_ip:
            filtered = [
                p for p in filtered
                if p.get('ip', {}).get('src_ip') == src_ip
            ]
        
        # Filter by destination IP
        if dst_ip:
            filtered = [
                p for p in filtered
                if p.get('ip', {}).get('dst_ip') == dst_ip
            ]
        
        # Filter by source port
        if src_port:
            filtered = [
                p for p in filtered
                if p.get('tcp', {}).get('src_port') == src_port or
                   p.get('udp', {}).get('src_port') == src_port
            ]
        
        # Filter by destination port
        if dst_port:
            filtered = [
                p for p in filtered
                if p.get('tcp', {}).get('dst_port') == dst_port or
                   p.get('udp', {}).get('dst_port') == dst_port
            ]
        
        return filtered
    
    def get_packet_summary(self, packet_info: Dict[str, Any]) -> str:
        """
        Get human-readable packet summary.
        
        Args:
            packet_info: Packet information dictionary
            
        Returns:
            Formatted packet summary string
        """
        protocols = ' -> '.join(packet_info.get('protocols', []))
        
        summary_parts = [
            f"Packet #{packet_info.get('packet_number', '?')}",
            f"Length: {packet_info.get('raw_length', 0)} bytes",
            f"Protocols: {protocols}",
        ]
        
        if packet_info.get('ip'):
            ip_info = packet_info['ip']
            summary_parts.append(
                f"IP: {ip_info.get('src_ip', '?')} -> {ip_info.get('dst_ip', '?')}"
            )
        
        if packet_info.get('tcp'):
            tcp_info = packet_info['tcp']
            summary_parts.append(
                f"TCP: {tcp_info.get('src_port', '?')} -> {tcp_info.get('dst_port', '?')}"
            )
        
        if packet_info.get('udp'):
            udp_info = packet_info['udp']
            summary_parts.append(
                f"UDP: {udp_info.get('src_port', '?')} -> {udp_info.get('dst_port', '?')}"
            )
        
        return ' | '.join(summary_parts)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get capture statistics.
        
        Returns:
            Dictionary containing capture statistics
        """
        return {
            'packets_captured': self.stats.packets_captured,
            'bytes_captured': self.stats.bytes_captured,
            'packets_dropped': self.stats.packets_dropped,
            'duration_seconds': self.stats.duration_seconds,
            'packets_per_second': self.stats.packets_per_second,
            'is_capturing': self.is_capturing,
            'interface': self.interface,
            'buffer_size': self.buffer_size,
        }
    
    def stop_capture(self):
        """Stop ongoing capture"""
        self.is_capturing = False
    
    def clear_captured(self):
        """Clear captured packets list"""
        self.captured_packets.clear()
        self.stats = RawSocketStats()
        self.analyzer = PacketAnalyzer()
    
    @staticmethod
    def get_interfaces() -> List[str]:
        """
        Get list of available network interfaces.
        
        Returns:
            List of interface names
        """
        try:
            import netifaces
            return netifaces.interfaces()
        except ImportError:
            # Fallback: read from /proc/net/dev on Linux
            try:
                with open('/proc/net/dev', 'r') as f:
                    lines = f.readlines()[2:]  # Skip header lines
                    interfaces = []
                    for line in lines:
                        iface = line.split(':')[0].strip()
                        if iface:
                            interfaces.append(iface)
                    return interfaces
            except:
                return ['eth0', 'wlan0', 'lo']  # Default interfaces
