"""
Scapy Packet Capture Module

Provides high-level packet capture using Scapy library.
Scapy is a powerful Python library for packet manipulation and analysis.
"""

import time
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field

try:
    from scapy.all import sniff, wrpcap, rdpcap, Ether, IP, TCP, UDP, ICMP
    from scapy.layers.http import HTTPRequest, HTTPResponse
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("Warning: Scapy not installed. Install with: pip install scapy")


@dataclass
class CaptureStats:
    """Capture statistics"""
    packets_captured: int = 0
    packets_dropped: int = 0
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


class ScapyCapture:
    """
    High-level packet capture using Scapy.
    
    Features:
    - Live packet capture from network interfaces
    - Offline packet capture from PCAP files
    - Protocol filtering (TCP, UDP, ICMP, HTTP)
    - Packet saving to PCAP files
    - Real-time packet processing with callbacks
    """
    
    def __init__(self, interface: Optional[str] = None):
        """
        Initialize Scapy capture.
        
        Args:
            interface: Network interface to capture from (e.g., 'eth0', 'wlan0')
                      If None, uses default interface
        """
        if not SCAPY_AVAILABLE:
            raise ImportError("Scapy is not installed. Install with: pip install scapy")
        
        self.interface = interface
        self.captured_packets: List[Any] = []
        self.stats = CaptureStats()
        self.is_capturing = False
        self._callback: Optional[Callable] = None
    
    def capture_live(
        self,
        count: int = 0,
        timeout: Optional[int] = None,
        filter_expr: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> List[Any]:
        """
        Capture packets live from network interface.
        
        Args:
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
            filter_expr: BPF filter expression (e.g., 'tcp port 80')
            callback: Callback function for each packet
            
        Returns:
            List of captured packets
        """
        if not SCAPY_AVAILABLE:
            raise ImportError("Scapy is not installed")
        
        self.is_capturing = True
        self.stats.start_time = datetime.now()
        self._callback = callback
        
        def packet_handler(packet):
            self.captured_packets.append(packet)
            self.stats.packets_captured += 1
            self.stats.bytes_captured += len(packet)
            
            if self._callback:
                self._callback(packet)
        
        try:
            sniff(
                iface=self.interface,
                count=count,
                timeout=timeout,
                filter=filter_expr,
                prn=packet_handler,
                store=0
            )
        finally:
            self.is_capturing = False
            self.stats.end_time = datetime.now()
        
        return self.captured_packets
    
    def capture_to_file(
        self,
        filename: str,
        count: int = 0,
        timeout: Optional[int] = None,
        filter_expr: Optional[str] = None
    ) -> CaptureStats:
        """
        Capture packets and save to PCAP file.
        
        Args:
            filename: Output PCAP filename
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
            filter_expr: BPF filter expression
            
        Returns:
            Capture statistics
        """
        if not SCAPY_AVAILABLE:
            raise ImportError("Scapy is not installed")
        
        self.is_capturing = True
        self.stats.start_time = datetime.now()
        packets = []
        
        def packet_handler(packet):
            packets.append(packet)
            self.stats.packets_captured += 1
            self.stats.bytes_captured += len(packet)
        
        try:
            sniff(
                iface=self.interface,
                count=count,
                timeout=timeout,
                filter=filter_expr,
                prn=packet_handler,
                store=0
            )
            
            # Save to PCAP file
            wrpcap(filename, packets)
            
        finally:
            self.is_capturing = False
            self.stats.end_time = datetime.now()
        
        return self.stats
    
    def read_pcap(self, filename: str) -> List[Any]:
        """
        Read packets from PCAP file.
        
        Args:
            filename: Input PCAP filename
            
        Returns:
            List of packets
        """
        if not SCAPY_AVAILABLE:
            raise ImportError("Scapy is not installed")
        
        packets = rdpcap(filename)
        self.captured_packets = list(packets)
        self.stats.packets_captured = len(packets)
        
        return self.captured_packets
    
    def filter_packets(
        self,
        packets: Optional[List[Any]] = None,
        protocol: Optional[str] = None,
        src_ip: Optional[str] = None,
        dst_ip: Optional[str] = None,
        src_port: Optional[int] = None,
        dst_port: Optional[int] = None
    ) -> List[Any]:
        """
        Filter captured packets by various criteria.
        
        Args:
            packets: List of packets to filter (uses captured_packets if None)
            protocol: Protocol to filter ('tcp', 'udp', 'icmp', 'http')
            src_ip: Source IP address
            dst_ip: Destination IP address
            src_port: Source port number
            dst_port: Destination port number
            
        Returns:
            Filtered list of packets
        """
        if not SCAPY_AVAILABLE:
            raise ImportError("Scapy is not installed")
        
        if packets is None:
            packets = self.captured_packets
        
        filtered = packets
        
        # Filter by protocol
        if protocol:
            protocol = protocol.lower()
            if protocol == 'tcp':
                filtered = [p for p in filtered if TCP in p]
            elif protocol == 'udp':
                filtered = [p for p in filtered if UDP in p]
            elif protocol == 'icmp':
                filtered = [p for p in filtered if ICMP in p]
            elif protocol == 'http':
                filtered = [p for p in filtered if HTTPRequest in p or HTTPResponse in p]
        
        # Filter by source IP
        if src_ip:
            filtered = [p for p in filtered if IP in p and p[IP].src == src_ip]
        
        # Filter by destination IP
        if dst_ip:
            filtered = [p for p in filtered if IP in p and p[IP].dst == dst_ip]
        
        # Filter by source port
        if src_port:
            filtered = [
                p for p in filtered
                if (TCP in p and p[TCP].sport == src_port) or
                   (UDP in p and p[UDP].sport == src_port)
            ]
        
        # Filter by destination port
        if dst_port:
            filtered = [
                p for p in filtered
                if (TCP in p and p[TCP].dport == dst_port) or
                   (UDP in p and p[UDP].dport == dst_port)
            ]
        
        return filtered
    
    def get_packet_summary(self, packet: Any) -> Dict[str, Any]:
        """
        Get summary information for a packet.
        
        Args:
            packet: Scapy packet object
            
        Returns:
            Dictionary containing packet summary
        """
        if not SCAPY_AVAILABLE:
            raise ImportError("Scapy is not installed")
        
        summary = {
            'length': len(packet),
            'time': datetime.fromtimestamp(packet.time).isoformat() if hasattr(packet, 'time') else None,
            'protocols': [],
        }
        
        # Check for Ethernet
        if Ether in packet:
            summary['protocols'].append('Ethernet')
            summary['src_mac'] = packet[Ether].src
            summary['dst_mac'] = packet[Ether].dst
        
        # Check for IP
        if IP in packet:
            summary['protocols'].append('IP')
            summary['src_ip'] = packet[IP].src
            summary['dst_ip'] = packet[IP].dst
            summary['ttl'] = packet[IP].ttl
            summary['ip_length'] = packet[IP].len
        
        # Check for TCP
        if TCP in packet:
            summary['protocols'].append('TCP')
            summary['src_port'] = packet[TCP].sport
            summary['dst_port'] = packet[TCP].dport
            summary['tcp_flags'] = str(packet[TCP].flags)
            summary['seq'] = packet[TCP].seq
            summary['ack'] = packet[TCP].ack
        
        # Check for UDP
        if UDP in packet:
            summary['protocols'].append('UDP')
            summary['src_port'] = packet[UDP].sport
            summary['dst_port'] = packet[UDP].dport
            summary['udp_length'] = packet[UDP].len
        
        # Check for ICMP
        if ICMP in packet:
            summary['protocols'].append('ICMP')
            summary['icmp_type'] = packet[ICMP].type
            summary['icmp_code'] = packet[ICMP].code
        
        # Check for HTTP
        if HTTPRequest in packet:
            summary['protocols'].append('HTTP-Request')
            summary['http_method'] = packet[HTTPRequest].Method.decode()
            summary['http_host'] = packet[HTTPRequest].Host.decode()
            summary['http_path'] = packet[HTTPRequest].Path.decode()
        
        if HTTPResponse in packet:
            summary['protocols'].append('HTTP-Response')
            summary['http_status'] = packet[HTTPResponse].Status_Code
        
        return summary
    
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
        }
    
    def stop_capture(self):
        """Stop ongoing capture"""
        self.is_capturing = False
    
    def clear_captured(self):
        """Clear captured packets list"""
        self.captured_packets.clear()
        self.stats = CaptureStats()
