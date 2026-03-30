"""
Network Monitor Module

Main interface for network monitoring and packet capture.
Provides unified access to all capture methods.
"""

import os
import json
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

from .scapy_capture import ScapyCapture
from .raw_socket_capture import RawSocketCapture
from .libpcap_capture import LibpcapCapture
from .ebpf_capture import EBpfCapture
from .cli_capture import CliCapture
from .netfilter_capture import NetfilterCapture
from .packet_analyzer import PacketAnalyzer


@dataclass
class CaptureConfig:
    """Capture configuration"""
    method: str = 'scapy'
    interface: Optional[str] = None
    count: int = 0
    timeout: Optional[int] = None
    filter_expr: Optional[str] = None
    output_file: Optional[str] = None
    promisc: bool = True
    snaplen: int = 65535
    queue_num: int = 1
    backend: str = 'bcc'
    tool: str = 'tshark'


class NetworkMonitor:
    """
    Unified network monitoring interface.
    
    Provides access to all packet capture methods:
    - Scapy: High-level packet manipulation
    - Raw Sockets: Low-level AF_PACKET capture
    - libpcap: Industry-standard capture library
    - eBPF: Kernel-level high-performance capture
    - CLI Tools: TShark/tcpdump integration
    - NetfilterQueue: Userspace packet filtering
    
    Example usage:
        monitor = NetworkMonitor()
        
        # Capture with Scapy
        packets = monitor.capture(method='scapy', count=10)
        
        # Capture with raw sockets
        packets = monitor.capture(method='raw_socket', interface='eth0')
        
        # Capture with eBPF
        packets = monitor.capture(method='ebpf', interface='eth0')
    """
    
    SUPPORTED_METHODS = [
        'scapy',
        'raw_socket',
        'libpcap',
        'ebpf',
        'cli',
        'netfilter'
    ]
    
    def __init__(self):
        """Initialize network monitor"""
        self.analyzer = PacketAnalyzer()
        self.captured_packets: List[Dict[str, Any]] = []
        self.capture_stats: Dict[str, Any] = {}
        self._capture_instance = None
    
    def capture(
        self,
        method: str = 'scapy',
        interface: Optional[str] = None,
        count: int = 0,
        timeout: Optional[int] = None,
        filter_expr: Optional[str] = None,
        callback: Optional[Callable] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Capture packets using specified method.
        
        Args:
            method: Capture method ('scapy', 'raw_socket', 'libpcap', 'ebpf', 'cli', 'netfilter')
            interface: Network interface to capture from
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
            filter_expr: Filter expression (BPF for most methods)
            callback: Callback function for each packet
            **kwargs: Additional method-specific arguments
            
        Returns:
            List of captured packet dictionaries
        """
        method = method.lower()
        
        if method not in self.SUPPORTED_METHODS:
            raise ValueError(
                f"Unsupported method: {method}. "
                f"Supported methods: {', '.join(self.SUPPORTED_METHODS)}"
            )
        
        # Clear previous captures
        self.captured_packets.clear()
        
        # Capture based on method
        if method == 'scapy':
            self.captured_packets = self._capture_scapy(
                interface, count, timeout, filter_expr, callback, **kwargs
            )
        elif method == 'raw_socket':
            self.captured_packets = self._capture_raw_socket(
                interface, count, timeout, callback, **kwargs
            )
        elif method == 'libpcap':
            self.captured_packets = self._capture_libpcap(
                interface, count, filter_expr, callback, **kwargs
            )
        elif method == 'ebpf':
            self.captured_packets = self._capture_ebpf(
                interface, count, timeout, callback, **kwargs
            )
        elif method == 'cli':
            self.captured_packets = self._capture_cli(
                interface, count, timeout, filter_expr, callback, **kwargs
            )
        elif method == 'netfilter':
            self.captured_packets = self._capture_netfilter(
                count, timeout, callback, **kwargs
            )
        
        return self.captured_packets
    
    def _capture_scapy(
        self,
        interface: Optional[str],
        count: int,
        timeout: Optional[int],
        filter_expr: Optional[str],
        callback: Optional[Callable],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Capture using Scapy"""
        try:
            capture = ScapyCapture(interface=interface)
            self._capture_instance = capture
            
            packets = capture.capture_live(
                count=count,
                timeout=timeout,
                filter_expr=filter_expr,
                callback=callback
            )
            
            self.capture_stats = capture.get_stats()
            
            # Convert Scapy packets to dictionaries
            result = []
            for packet in packets:
                summary = capture.get_packet_summary(packet)
                result.append(summary)
            
            return result
            
        except ImportError as e:
            print(f"Scapy not available: {e}")
            return []
    
    def _capture_raw_socket(
        self,
        interface: Optional[str],
        count: int,
        timeout: Optional[int],
        callback: Optional[Callable],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Capture using raw sockets"""
        try:
            capture = RawSocketCapture(interface=interface)
            self._capture_instance = capture
            
            packets = capture.capture(
                count=count,
                timeout=timeout,
                callback=callback
            )
            
            self.capture_stats = capture.get_stats()
            return packets
            
        except PermissionError as e:
            print(f"Permission denied: {e}")
            print("Run with sudo or grant CAP_NET_RAW capability")
            return []
        except Exception as e:
            print(f"Error capturing with raw sockets: {e}")
            return []
    
    def _capture_libpcap(
        self,
        interface: Optional[str],
        count: int,
        filter_expr: Optional[str],
        callback: Optional[Callable],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Capture using libpcap"""
        try:
            capture = LibpcapCapture(interface=interface)
            self._capture_instance = capture
            
            packets = capture.capture(
                count=count,
                filter_expr=filter_expr,
                callback=callback
            )
            
            self.capture_stats = capture.get_stats()
            return packets
            
        except ImportError as e:
            print(f"libpcap not available: {e}")
            return []
        except Exception as e:
            print(f"Error capturing with libpcap: {e}")
            return []
    
    def _capture_ebpf(
        self,
        interface: Optional[str],
        count: int,
        timeout: Optional[int],
        callback: Optional[Callable],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Capture using eBPF"""
        try:
            backend = kwargs.get('backend', 'bcc')
            capture = EBpfCapture(interface=interface, backend=backend)
            self._capture_instance = capture
            
            # Try XDP first, fall back to kprobe
            try:
                packets = capture.capture_xdp(
                    count=count,
                    timeout=timeout,
                    callback=callback
                )
            except Exception as e:
                print(f"XDP capture failed, trying kprobe: {e}")
                packets = capture.capture_kprobe(
                    count=count,
                    timeout=timeout,
                    callback=callback
                )
            
            self.capture_stats = capture.get_stats()
            return packets
            
        except ImportError as e:
            print(f"eBPF not available: {e}")
            return []
        except Exception as e:
            print(f"Error capturing with eBPF: {e}")
            return []
    
    def _capture_cli(
        self,
        interface: Optional[str],
        count: int,
        timeout: Optional[int],
        filter_expr: Optional[str],
        callback: Optional[Callable],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Capture using CLI tools"""
        try:
            tool = kwargs.get('tool', 'tshark')
            capture = CliCapture(interface=interface, tool=tool)
            self._capture_instance = capture
            
            packets = capture.capture(
                count=count,
                timeout=timeout,
                filter_expr=filter_expr,
                callback=callback
            )
            
            self.capture_stats = capture.get_stats()
            return packets
            
        except FileNotFoundError as e:
            print(f"CLI tool not found: {e}")
            return []
        except Exception as e:
            print(f"Error capturing with CLI: {e}")
            return []
    
    def _capture_netfilter(
        self,
        count: int,
        timeout: Optional[int],
        callback: Optional[Callable],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Capture using NetfilterQueue"""
        try:
            queue_num = kwargs.get('queue_num', 1)
            capture = NetfilterCapture(queue_num=queue_num)
            self._capture_instance = capture
            
            packets = capture.capture(
                count=count,
                timeout=timeout,
                callback=callback
            )
            
            self.capture_stats = capture.get_stats()
            return packets
            
        except ImportError as e:
            print(f"NetfilterQueue not available: {e}")
            return []
        except Exception as e:
            print(f"Error capturing with NetfilterQueue: {e}")
            return []
    
    def capture_to_file(
        self,
        filename: str,
        method: str = 'scapy',
        interface: Optional[str] = None,
        count: int = 0,
        timeout: Optional[int] = None,
        filter_expr: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Capture packets to PCAP file.
        
        Args:
            filename: Output PCAP filename
            method: Capture method
            interface: Network interface
            count: Number of packets to capture
            timeout: Timeout in seconds
            filter_expr: Filter expression
            **kwargs: Additional arguments
            
        Returns:
            Capture statistics
        """
        method = method.lower()
        
        if method == 'scapy':
            try:
                capture = ScapyCapture(interface=interface)
                stats = capture.capture_to_file(
                    filename=filename,
                    count=count,
                    timeout=timeout,
                    filter_expr=filter_expr
                )
                return asdict(stats)
            except Exception as e:
                print(f"Error capturing to file: {e}")
                return {}
        
        elif method == 'cli':
            try:
                tool = kwargs.get('tool', 'tshark')
                capture = CliCapture(interface=interface, tool=tool)
                stats = capture.capture_to_file(
                    filename=filename,
                    count=count,
                    timeout=timeout,
                    filter_expr=filter_expr
                )
                return asdict(stats)
            except Exception as e:
                print(f"Error capturing to file: {e}")
                return {}
        
        else:
            print(f"File capture not supported for method: {method}")
            return {}
    
    def read_pcap(
        self,
        filename: str,
        method: str = 'scapy',
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Read packets from PCAP file.
        
        Args:
            filename: Input PCAP filename
            method: Method to use for reading
            **kwargs: Additional arguments
            
        Returns:
            List of packet dictionaries
        """
        method = method.lower()
        
        if method == 'scapy':
            try:
                capture = ScapyCapture()
                packets = capture.read_pcap(filename)
                
                result = []
                for packet in packets:
                    summary = capture.get_packet_summary(packet)
                    result.append(summary)
                
                return result
            except Exception as e:
                print(f"Error reading PCAP: {e}")
                return []
        
        elif method == 'cli':
            try:
                tool = kwargs.get('tool', 'tshark')
                capture = CliCapture(tool=tool)
                return capture.read_pcap(filename)
            except Exception as e:
                print(f"Error reading PCAP: {e}")
                return []
        
        else:
            print(f"PCAP reading not supported for method: {method}")
            return []
    
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
        Filter packets by various criteria.
        
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
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get capture statistics.
        
        Returns:
            Dictionary containing capture statistics
        """
        return self.capture_stats
    
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
    
    def export_to_json(
        self,
        filename: str,
        packets: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Export captured packets to JSON file.
        
        Args:
            filename: Output JSON filename
            packets: List of packets to export (uses captured_packets if None)
        """
        if packets is None:
            packets = self.captured_packets
        
        # Remove raw_data from export (too large)
        export_data = []
        for packet in packets:
            packet_copy = packet.copy()
            if 'raw_data' in packet_copy:
                del packet_copy['raw_data']
            export_data.append(packet_copy)
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"Exported {len(export_data)} packets to {filename}")
    
    def stop_capture(self):
        """Stop ongoing capture"""
        if self._capture_instance:
            self._capture_instance.stop_capture()
    
    def clear_captured(self):
        """Clear captured packets"""
        self.captured_packets.clear()
        self.capture_stats.clear()
        self.analyzer = PacketAnalyzer()
    
    @staticmethod
    def get_available_methods() -> List[str]:
        """
        Get list of available capture methods.
        
        Returns:
            List of available method names
        """
        available = []
        
        # Check Scapy
        try:
            import scapy.all
            available.append('scapy')
        except ImportError:
            pass
        
        # Check raw sockets (Linux only)
        try:
            import socket
            sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
            sock.close()
            available.append('raw_socket')
        except:
            pass
        
        # Check libpcap
        try:
            import pcapy
            available.append('libpcap')
        except ImportError:
            pass
        
        # Check eBPF
        try:
            from bcc import BPF
            available.append('ebpf')
        except ImportError:
            pass
        
        # Check CLI tools
        try:
            import subprocess
            subprocess.run(['which', 'tshark'], capture_output=True, check=True)
            available.append('cli')
        except:
            pass
        
        # Check NetfilterQueue
        try:
            from netfilterqueue import NetfilterQueue
            available.append('netfilter')
        except ImportError:
            pass
        
        return available
    
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
