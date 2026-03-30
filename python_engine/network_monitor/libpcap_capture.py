"""
libpcap Packet Capture Module

Provides packet capture using libpcap wrappers (pcapy, pylibpcap, PyPcap).
libpcap is the industry-standard library for portable packet capture.
"""

import time
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from .packet_analyzer import PacketAnalyzer

try:
    import pcapy
    PCAPY_AVAILABLE = True
except ImportError:
    PCAPY_AVAILABLE = False
    print("Warning: pcapy not installed. Install with: pip install pcapy")

try:
    import pylibpcap
    PYLIBPCAP_AVAILABLE = True
except ImportError:
    PYLIBPCAP_AVAILABLE = False

try:
    import pypcap
    PYPCAP_AVAILABLE = True
except ImportError:
    PYPCAP_AVAILABLE = False


@dataclass
class LibpcapStats:
    """libpcap capture statistics"""
    packets_captured: int = 0
    bytes_captured: int = 0
    packets_dropped: int = 0
    packets_if_dropped: int = 0
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


class LibpcapCapture:
    """
    Packet capture using libpcap wrappers.
    
    Features:
    - Industry-standard libpcap library
    - BPF filter support
    - Cross-platform (Linux, macOS, Windows with WinPcap/Npcap)
    - High performance packet capture
    - PCAP file reading/writing
    
    Supported backends:
    - pcapy: Python wrapper for libpcap
    - pylibpcap: Alternative libpcap wrapper
    - pypcap: Another libpcap wrapper
    """
    
    def __init__(
        self,
        interface: Optional[str] = None,
        snaplen: int = 65535,
        promisc: bool = True,
        timeout: int = 100
    ):
        """
        Initialize libpcap capture.
        
        Args:
            interface: Network interface to capture from
            snaplen: Snapshot length (bytes to capture per packet)
            promisc: Enable promiscuous mode
            timeout: Read timeout in milliseconds
        """
        self.interface = interface
        self.snaplen = snaplen
        self.promisc = promisc
        self.timeout = timeout
        
        self.analyzer = PacketAnalyzer()
        self.stats = LibpcapStats()
        self.is_capturing = False
        self.captured_packets: List[Dict[str, Any]] = []
        self._callback: Optional[Callable] = None
        self._pcap = None
        
        # Determine available backend
        self.backend = self._detect_backend()
    
    def _detect_backend(self) -> str:
        """
        Detect available libpcap backend.
        
        Returns:
            Name of available backend
        """
        if PCAPY_AVAILABLE:
            return 'pcapy'
        elif PYLIBPCAP_AVAILABLE:
            return 'pylibpcap'
        elif PYPCAP_AVAILABLE:
            return 'pypcap'
        else:
            raise ImportError(
                "No libpcap wrapper available. Install one of: "
                "pcapy, pylibpcap, or pypcap"
            )
    
    def _create_pcapy_capture(self, filter_expr: Optional[str] = None):
        """
        Create pcapy capture object.
        
        Args:
            filter_expr: BPF filter expression
            
        Returns:
            pcapy capture object
        """
        if not PCAPY_AVAILABLE:
            raise ImportError("pcapy not installed")
        
        # Open interface for capture
        pcap = pcapy.open_live(
            self.interface,
            self.snaplen,
            self.promisc,
            self.timeout
        )
        
        # Set BPF filter if provided
        if filter_expr:
            pcap.setfilter(filter_expr)
        
        return pcap
    
    def _create_pylibpcap_capture(self, filter_expr: Optional[str] = None):
        """
        Create pylibpcap capture object.
        
        Args:
            filter_expr: BPF filter expression
            
        Returns:
            pylibpcap capture object
        """
        if not PYLIBPCAP_AVAILABLE:
            raise ImportError("pylibpcap not installed")
        
        # Open interface for capture
        pcap = pylibpcap.pcapObject(self.interface)
        
        # Set BPF filter if provided
        if filter_expr:
            pcap.setfilter(filter_expr)
        
        return pcap
    
    def _create_pypcap_capture(self, filter_expr: Optional[str] = None):
        """
        Create pypcap capture object.
        
        Args:
            filter_expr: BPF filter expression
            
        Returns:
            pypcap capture object
        """
        if not PYPCAP_AVAILABLE:
            raise ImportError("pypcap not installed")
        
        # Open interface for capture
        pcap = pypcap.pcap(self.interface)
        
        # Set BPF filter if provided
        if filter_expr:
            pcap.setfilter(filter_expr)
        
        return pcap
    
    def capture(
        self,
        count: int = 0,
        filter_expr: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Capture packets from network interface.
        
        Args:
            count: Number of packets to capture (0 = unlimited)
            filter_expr: BPF filter expression
            callback: Callback function for each packet
            
        Returns:
            List of captured packet dictionaries
        """
        self.is_capturing = True
        self.stats.start_time = datetime.now()
        self._callback = callback
        
        try:
            # Create capture object based on backend
            if self.backend == 'pcapy':
                self._pcap = self._create_pcapy_capture(filter_expr)
                return self._capture_pcapy(count)
            elif self.backend == 'pylibpcap':
                self._pcap = self._create_pylibpcap_capture(filter_expr)
                return self._capture_pylibpcap(count)
            elif self.backend == 'pypcap':
                self._pcap = self._create_pypcap_capture(filter_expr)
                return self._capture_pypcap(count)
        finally:
            self.is_capturing = False
            self.stats.end_time = datetime.now()
    
    def _capture_pcapy(self, count: int) -> List[Dict[str, Any]]:
        """
        Capture packets using pcapy.
        
        Args:
            count: Number of packets to capture
            
        Returns:
            List of captured packet dictionaries
        """
        packets_captured = 0
        
        def packet_handler(header, data):
            nonlocal packets_captured
            
            if count > 0 and packets_captured >= count:
                return
            
            # Parse packet
            packet_info = self.analyzer.analyze_packet(data)
            packet_info['raw_data'] = data
            packet_info['interface'] = self.interface
            
            # Update statistics
            self.stats.packets_captured += 1
            self.stats.bytes_captured += len(data)
            packets_captured += 1
            
            # Store packet
            self.captured_packets.append(packet_info)
            
            # Call callback if provided
            if self._callback:
                self._callback(packet_info)
        
        # Start capture loop
        while self.is_capturing:
            if count > 0 and packets_captured >= count:
                break
            
            try:
                self._pcap.dispatch(1, packet_handler)
            except Exception as e:
                print(f"Error capturing packet: {e}")
                self.stats.packets_dropped += 1
                continue
        
        return self.captured_packets
    
    def _capture_pylibpcap(self, count: int) -> List[Dict[str, Any]]:
        """
        Capture packets using pylibpcap.
        
        Args:
            count: Number of packets to capture
            
        Returns:
            List of captured packet dictionaries
        """
        packets_captured = 0
        
        while self.is_capturing:
            if count > 0 and packets_captured >= count:
                break
            
            try:
                # Capture packet
                packet = self._pcap.next()
                if packet is None:
                    continue
                
                # Parse packet
                packet_info = self.analyzer.analyze_packet(packet)
                packet_info['raw_data'] = packet
                packet_info['interface'] = self.interface
                
                # Update statistics
                self.stats.packets_captured += 1
                self.stats.bytes_captured += len(packet)
                packets_captured += 1
                
                # Store packet
                self.captured_packets.append(packet_info)
                
                # Call callback if provided
                if self._callback:
                    self._callback(packet_info)
                    
            except Exception as e:
                print(f"Error capturing packet: {e}")
                self.stats.packets_dropped += 1
                continue
        
        return self.captured_packets
    
    def _capture_pypcap(self, count: int) -> List[Dict[str, Any]]:
        """
        Capture packets using pypcap.
        
        Args:
            count: Number of packets to capture
            
        Returns:
            List of captured packet dictionaries
        """
        packets_captured = 0
        
        for timestamp, packet in self._pcap:
            if not self.is_capturing:
                break
            
            if count > 0 and packets_captured >= count:
                break
            
            try:
                # Parse packet
                packet_info = self.analyzer.analyze_packet(packet)
                packet_info['raw_data'] = packet
                packet_info['interface'] = self.interface
                packet_info['timestamp'] = timestamp
                
                # Update statistics
                self.stats.packets_captured += 1
                self.stats.bytes_captured += len(packet)
                packets_captured += 1
                
                # Store packet
                self.captured_packets.append(packet_info)
                
                # Call callback if provided
                if self._callback:
                    self._callback(packet_info)
                    
            except Exception as e:
                print(f"Error capturing packet: {e}")
                self.stats.packets_dropped += 1
                continue
        
        return self.captured_packets
    
    def read_pcap(self, filename: str) -> List[Dict[str, Any]]:
        """
        Read packets from PCAP file.
        
        Args:
            filename: Input PCAP filename
            
        Returns:
            List of packet dictionaries
        """
        if self.backend == 'pcapy':
            return self._read_pcap_pcapy(filename)
        elif self.backend == 'pylibpcap':
            return self._read_pcap_pylibpcap(filename)
        elif self.backend == 'pypcap':
            return self._read_pcap_pypcap(filename)
    
    def _read_pcap_pcapy(self, filename: str) -> List[Dict[str, Any]]:
        """Read PCAP file using pcapy"""
        if not PCAPY_AVAILABLE:
            raise ImportError("pcapy not installed")
        
        pcap = pcapy.open_offline(filename)
        packets = []
        
        def packet_handler(header, data):
            packet_info = self.analyzer.analyze_packet(data)
            packet_info['raw_data'] = data
            packets.append(packet_info)
        
        pcap.dispatch(-1, packet_handler)
        
        self.captured_packets = packets
        self.stats.packets_captured = len(packets)
        
        return packets
    
    def _read_pcap_pylibpcap(self, filename: str) -> List[Dict[str, Any]]:
        """Read PCAP file using pylibpcap"""
        if not PYLIBPCAP_AVAILABLE:
            raise ImportError("pylibpcap not installed")
        
        pcap = pylibpcap.pcapObject(filename)
        packets = []
        
        while True:
            packet = pcap.next()
            if packet is None:
                break
            
            packet_info = self.analyzer.analyze_packet(packet)
            packet_info['raw_data'] = packet
            packets.append(packet_info)
        
        self.captured_packets = packets
        self.stats.packets_captured = len(packets)
        
        return packets
    
    def _read_pcap_pypcap(self, filename: str) -> List[Dict[str, Any]]:
        """Read PCAP file using pypcap"""
        if not PYPCAP_AVAILABLE:
            raise ImportError("pypcap not installed")
        
        pcap = pypcap.pcap(filename)
        packets = []
        
        for timestamp, packet in pcap:
            packet_info = self.analyzer.analyze_packet(packet)
            packet_info['raw_data'] = packet
            packet_info['timestamp'] = timestamp
            packets.append(packet_info)
        
        self.captured_packets = packets
        self.stats.packets_captured = len(packets)
        
        return packets
    
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
            'packets_if_dropped': self.stats.packets_if_dropped,
            'duration_seconds': self.stats.duration_seconds,
            'packets_per_second': self.stats.packets_per_second,
            'is_capturing': self.is_capturing,
            'interface': self.interface,
            'backend': self.backend,
            'snaplen': self.snaplen,
            'promisc': self.promisc,
        }
    
    def stop_capture(self):
        """Stop ongoing capture"""
        self.is_capturing = False
    
    def clear_captured(self):
        """Clear captured packets list"""
        self.captured_packets.clear()
        self.stats = LibpcapStats()
        self.analyzer = PacketAnalyzer()
    
    @staticmethod
    def get_interfaces() -> List[str]:
        """
        Get list of available network interfaces.
        
        Returns:
            List of interface names
        """
        if PCAPY_AVAILABLE:
            return pcapy.findalldevs()
        elif PYLIBPCAP_AVAILABLE:
            return pylibpcap.findalldevs()
        elif PYPCAP_AVAILABLE:
            return pypcap.findalldevs()
        else:
            return []
