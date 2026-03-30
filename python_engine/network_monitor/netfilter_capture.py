"""
NetfilterQueue Packet Capture Module

Provides packet capture and filtering using NetfilterQueue.
This allows userspace packet processing via iptables/nftables rules.
"""

import socket
import struct
import time
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from .packet_analyzer import PacketAnalyzer

try:
    from netfilterqueue import NetfilterQueue as NFQueue
    NETFILTERQUEUE_AVAILABLE = True
except ImportError:
    NETFILTERQUEUE_AVAILABLE = False
    print("Warning: NetfilterQueue not installed. Install with: pip install NetfilterQueue")


@dataclass
class NetfilterStats:
    """NetfilterQueue capture statistics"""
    packets_captured: int = 0
    bytes_captured: int = 0
    packets_accepted: int = 0
    packets_dropped: int = 0
    packets_modified: int = 0
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


class NetfilterCapture:
    """
    Packet capture and filtering using NetfilterQueue.
    
    Features:
    - Userspace packet processing via iptables/nftables
    - Packet inspection and modification
    - Accept, drop, or modify packets
    - Queue-based processing
    - Integration with Linux firewall
    
    Note:
        Requires root privileges and iptables/nftables rules to be set up
        Linux-specific (NetfilterQueue is not available on Windows/macOS)
    """
    
    # Netfilter verdict constants
    NF_DROP = 0
    NF_ACCEPT = 1
    NF_STOLEN = 2
    NF_QUEUE = 3
    NF_REPEAT = 4
    NF_STOP = 5
    
    def __init__(
        self,
        queue_num: int = 1,
        max_queue_len: int = 65535
    ):
        """
        Initialize NetfilterQueue capture.
        
        Args:
            queue_num: Netfilter queue number (must match iptables rule)
            max_queue_len: Maximum queue length
        """
        if not NETFILTERQUEUE_AVAILABLE:
            raise ImportError(
                "NetfilterQueue not installed. Install with: pip install NetfilterQueue"
            )
        
        self.queue_num = queue_num
        self.max_queue_len = max_queue_len
        
        self.analyzer = PacketAnalyzer()
        self.stats = NetfilterStats()
        self.is_capturing = False
        self.captured_packets: List[Dict[str, Any]] = []
        self._callback: Optional[Callable] = None
        self._nfqueue: Optional[NFQueue] = None
        self._default_verdict = self.NF_ACCEPT
    
    def _packet_handler(self, packet):
        """
        Handle incoming packet from NetfilterQueue.
        
        Args:
            packet: NetfilterQueue packet object
        """
        if not self.is_capturing:
            packet.accept()
            return
        
        try:
            # Get raw packet data
            raw_data = packet.get_payload()
            
            # Parse packet
            packet_info = self.analyzer.analyze_packet(raw_data)
            packet_info['raw_data'] = raw_data
            packet_info['queue_num'] = self.queue_num
            packet_info['packet_id'] = packet.get_hw_len()
            
            # Update statistics
            self.stats.packets_captured += 1
            self.stats.bytes_captured += len(raw_data)
            
            # Store packet
            self.captured_packets.append(packet_info)
            
            # Call callback if provided
            if self._callback:
                verdict = self._callback(packet_info)
                
                # Apply verdict
                if verdict == self.NF_DROP:
                    packet.drop()
                    self.stats.packets_dropped += 1
                elif verdict == self.NF_ACCEPT:
                    packet.accept()
                    self.stats.packets_accepted += 1
                elif verdict == self.NF_REPEAT:
                    packet.repeat()
                else:
                    # Default verdict
                    if self._default_verdict == self.NF_DROP:
                        packet.drop()
                        self.stats.packets_dropped += 1
                    else:
                        packet.accept()
                        self.stats.packets_accepted += 1
            else:
                # No callback, use default verdict
                if self._default_verdict == self.NF_DROP:
                    packet.drop()
                    self.stats.packets_dropped += 1
                else:
                    packet.accept()
                    self.stats.packets_accepted += 1
                    
        except Exception as e:
            print(f"Error processing packet: {e}")
            packet.accept()
            self.stats.packets_accepted += 1
    
    def capture(
        self,
        count: int = 0,
        timeout: Optional[float] = None,
        callback: Optional[Callable] = None,
        default_verdict: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Capture packets from NetfilterQueue.
        
        Args:
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
            callback: Callback function for each packet
                     Should return verdict: NF_DROP, NF_ACCEPT, or NF_REPEAT
            default_verdict: Default verdict when no callback or callback returns None
            
        Returns:
            List of captured packet dictionaries
        """
        if not NETFILTERQUEUE_AVAILABLE:
            raise ImportError("NetfilterQueue not installed")
        
        self.is_capturing = True
        self.stats.start_time = datetime.now()
        self._callback = callback
        self._default_verdict = default_verdict
        
        try:
            # Create NetfilterQueue object
            self._nfqueue = NFQueue()
            
            # Bind to queue
            self._nfqueue.bind(self.queue_num, self._packet_handler)
            
            # Set queue length
            self._nfqueue.set_queue_maxlen(self.max_queue_len)
            
            # Start processing
            packets_processed = 0
            start_time = time.time()
            
            while self.is_capturing:
                if count > 0 and packets_processed >= count:
                    break
                
                if timeout and (time.time() - start_time) >= timeout:
                    break
                
                try:
                    # Process one packet with timeout
                    self._nfqueue.run(timeout=1)
                    packets_processed += 1
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error processing queue: {e}")
                    continue
                    
        finally:
            self.is_capturing = False
            self.stats.end_time = datetime.now()
            
            if self._nfqueue:
                self._nfqueue.unbind()
                self._nfqueue = None
        
        return self.captured_packets
    
    def capture_with_iptables(
        self,
        iptables_rule: str,
        count: int = 0,
        timeout: Optional[float] = None,
        callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Capture packets with automatic iptables rule management.
        
        Args:
            iptables_rule: iptables rule to add (e.g., 'INPUT -j NFQUEUE --queue-num 1')
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
            callback: Callback function for each packet
            
        Returns:
            List of captured packet dictionaries
        """
        import subprocess
        
        # Add iptables rule
        try:
            subprocess.run(
                ['iptables', '-A'] + iptables_rule.split(),
                check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error adding iptables rule: {e}")
            return []
        
        try:
            # Capture packets
            return self.capture(count, timeout, callback)
        finally:
            # Remove iptables rule
            try:
                subprocess.run(
                    ['iptables', '-D'] + iptables_rule.split(),
                    check=True
                )
            except subprocess.CalledProcessError as e:
                print(f"Error removing iptables rule: {e}")
    
    def modify_packet(
        self,
        packet,
        modifications: Dict[str, Any]
    ) -> bytes:
        """
        Modify packet data.
        
        Args:
            packet: NetfilterQueue packet object
            modifications: Dictionary of modifications to apply
            
        Returns:
            Modified packet data
        """
        raw_data = bytearray(packet.get_payload())
        
        # Parse packet
        packet_info = self.analyzer.analyze_packet(bytes(raw_data))
        
        # Apply modifications
        if 'src_ip' in modifications and packet_info.get('ip'):
            # Modify source IP
            new_src_ip = socket.inet_aton(modifications['src_ip'])
            # IP header starts at byte 12 (source IP)
            raw_data[12:16] = new_src_ip
        
        if 'dst_ip' in modifications and packet_info.get('ip'):
            # Modify destination IP
            new_dst_ip = socket.inet_aton(modifications['dst_ip'])
            # IP header starts at byte 16 (destination IP)
            raw_data[16:20] = new_dst_ip
        
        if 'src_port' in modifications:
            if packet_info.get('tcp'):
                # Modify TCP source port
                new_src_port = struct.pack('!H', modifications['src_port'])
                # TCP header starts after IP header
                ip_header_len = packet_info['ip']['header_length']
                raw_data[ip_header_len:ip_header_len + 2] = new_src_port
            elif packet_info.get('udp'):
                # Modify UDP source port
                new_src_port = struct.pack('!H', modifications['src_port'])
                # UDP header starts after IP header
                ip_header_len = packet_info['ip']['header_length']
                raw_data[ip_header_len:ip_header_len + 2] = new_src_port
        
        if 'dst_port' in modifications:
            if packet_info.get('tcp'):
                # Modify TCP destination port
                new_dst_port = struct.pack('!H', modifications['dst_port'])
                # TCP header starts after IP header
                ip_header_len = packet_info['ip']['header_length']
                raw_data[ip_header_len + 2:ip_header_len + 4] = new_dst_port
            elif packet_info.get('udp'):
                # Modify UDP destination port
                new_dst_port = struct.pack('!H', modifications['dst_port'])
                # UDP header starts after IP header
                ip_header_len = packet_info['ip']['header_length']
                raw_data[ip_header_len + 2:ip_header_len + 4] = new_dst_port
        
        return bytes(raw_data)
    
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
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get capture statistics.
        
        Returns:
            Dictionary containing capture statistics
        """
        return {
            'packets_captured': self.stats.packets_captured,
            'bytes_captured': self.stats.bytes_captured,
            'packets_accepted': self.stats.packets_accepted,
            'packets_dropped': self.stats.packets_dropped,
            'packets_modified': self.stats.packets_modified,
            'duration_seconds': self.stats.duration_seconds,
            'packets_per_second': self.stats.packets_per_second,
            'is_capturing': self.is_capturing,
            'queue_num': self.queue_num,
            'max_queue_len': self.max_queue_len,
        }
    
    def stop_capture(self):
        """Stop ongoing capture"""
        self.is_capturing = False
    
    def clear_captured(self):
        """Clear captured packets list"""
        self.captured_packets.clear()
        self.stats = NetfilterStats()
        self.analyzer = PacketAnalyzer()
    
    @staticmethod
    def setup_iptables_rules(queue_num: int = 1):
        """
        Set up iptables rules for packet capture.
        
        Args:
            queue_num: Netfilter queue number
        """
        import subprocess
        
        rules = [
            ['iptables', '-A', 'INPUT', '-j', 'NFQUEUE', '--queue-num', str(queue_num)],
            ['iptables', '-A', 'OUTPUT', '-j', 'NFQUEUE', '--queue-num', str(queue_num)],
            ['iptables', '-A', 'FORWARD', '-j', 'NFQUEUE', '--queue-num', str(queue_num)],
        ]
        
        for rule in rules:
            try:
                subprocess.run(rule, check=True)
                print(f"Added rule: {' '.join(rule)}")
            except subprocess.CalledProcessError as e:
                print(f"Error adding rule: {e}")
    
    @staticmethod
    def cleanup_iptables_rules(queue_num: int = 1):
        """
        Clean up iptables rules.
        
        Args:
            queue_num: Netfilter queue number
        """
        import subprocess
        
        rules = [
            ['iptables', '-D', 'INPUT', '-j', 'NFQUEUE', '--queue-num', str(queue_num)],
            ['iptables', '-D', 'OUTPUT', '-j', 'NFQUEUE', '--queue-num', str(queue_num)],
            ['iptables', '-D', 'FORWARD', '-j', 'NFQUEUE', '--queue-num', str(queue_num)],
        ]
        
        for rule in rules:
            try:
                subprocess.run(rule, check=True)
                print(f"Removed rule: {' '.join(rule)}")
            except subprocess.CalledProcessError as e:
                print(f"Error removing rule: {e}")
